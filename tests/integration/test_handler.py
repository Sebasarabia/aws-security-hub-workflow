# SPDX-License-Identifier: MIT-0
"""Handler-level deterministic local behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyPersistenceLayerError
from botocore.stub import Stubber

from finding_processor import handler
from finding_processor.config import Settings
from finding_processor.exceptions import NotificationError
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


class BrokenSNS:
    def publish(self, **kwargs: object) -> dict:
        del kwargs
        raise RuntimeError("untrusted sns provider detail")


def test_sns_failure_is_application_failure(caplog: pytest.LogCaptureFixture) -> None:
    finding_event = event("fixtures/ocsf/high-severity.json")
    finding_event["detail"]["findings"][0]["finding_info"]["uid"] = "synthetic-sns-failure"
    with pytest.raises(NotificationError, match="sns_publish_failed"):
        process_event(finding_event, settings=settings(), sns_client=BrokenSNS())
    assert "untrusted sns provider detail" not in caplog.text
    assert "processing_failed" in caplog.text


def test_dynamodb_failure_is_application_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    client = handler.boto3.client("dynamodb", region_name="us-east-1")
    monkeypatch.setattr(handler, "_dynamodb", client)
    deployed_settings = settings()
    deployed_settings = deployed_settings.model_copy(
        update={"local_demo": False, "idempotency_table": "idempotency-test"}
    )
    with Stubber(client) as stubber:
        stubber.add_client_error(
            "put_item",
            service_error_code="InternalServerError",
            service_message="untrusted dynamodb provider detail",
            http_status_code=500,
        )
        with pytest.raises(IdempotencyPersistenceLayerError):
            process_event(
                event("fixtures/ocsf/high-severity.json"),
                settings=deployed_settings,
                lambda_context=FakeLambdaContext(),
            )
    assert "untrusted dynamodb provider detail" not in caplog.text
    assert "processing_failed" in caplog.text


class FakeLambdaContext:
    def get_remaining_time_in_millis(self) -> int:
        return 30_000
