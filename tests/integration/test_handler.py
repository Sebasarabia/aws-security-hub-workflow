"""Handler-level deterministic local behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from finding_processor.config import Settings
from finding_processor.handler import process_event

ROOT = Path(__file__).parents[2]


class FakeSNS:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def publish(self, **kwargs: Any) -> dict[str, str]:
        self.messages.append(kwargs["Message"])
        return {"MessageId": "test"}


def event(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def settings(mode: str = "dual") -> Settings:
    return Settings(
        finding_schema_mode=mode,
        local_demo=True,
        notification_topic_arn="arn:test",
        policy_path=str(ROOT / "config/triage-policy.json"),
    )


def test_ocsf_escalation_and_duplicate() -> None:
    sns = FakeSNS()
    first = process_event(event("fixtures/ocsf/high-severity.json"), settings=settings(), sns_client=sns)
    second = process_event(event("fixtures/ocsf/high-severity.json"), settings=settings(), sns_client=sns)
    assert first["decision"] == "ESCALATE"
    assert second["decision"] == "DUPLICATE"
    assert len(sns.messages) == 1


def test_asff_and_schema_mode_rejection() -> None:
    sns = FakeSNS()
    assert (
        process_event(event("fixtures/asff/high-severity.json"), settings=settings(), sns_client=sns)[
            "decision"
        ]
        == "ESCALATE"
    )
    assert (
        process_event(event("fixtures/asff/high-severity.json"), settings=settings("ocsf"), sns_client=sns)[
            "reason_code"
        ]
        == "SCHEMA_MODE_REJECTED"
    )


def test_malformed_rejected_without_raw_data(capsys: pytest.CaptureFixture[str]) -> None:
    bad = event("fixtures/ocsf/high-severity.json")
    bad["detail"]["findings"] = []
    assert process_event(bad, settings=settings(), sns_client=FakeSNS())["decision"] == "REJECT"
    assert "synthetic high-severity" not in capsys.readouterr().out.lower()
