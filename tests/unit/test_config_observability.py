# SPDX-License-Identifier: MIT-0
"""Configuration validation and safe observability behavior."""

from __future__ import annotations

import pytest

from finding_processor import observability
from finding_processor.config import ConfigurationError, load_settings


def test_invalid_runtime_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDEMPOTENCY_EXPIRY_SECONDS", "not-an-integer")
    with pytest.raises(ConfigurationError, match="invalid_runtime_configuration"):
        load_settings()


def test_metric_failure_is_safe(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def fail_metric(**kwargs: object) -> None:
        del kwargs
        raise RuntimeError("untrusted metric provider detail")

    monkeypatch.setattr(observability.metrics, "add_metric", fail_metric)
    assert observability.metric("FindingsReceived") is False
    assert "metric_emission_failed" in caplog.text
    assert "untrusted metric provider detail" not in caplog.text
