"""Notification minimization and idempotency semantics."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import boto3
import pytest
from botocore.stub import Stubber

from finding_processor.exceptions import NotificationError
from finding_processor.idempotency import LocalIdempotency, idempotency_key
from finding_processor.models import (
    DecisionType,
    NormalizedFinding,
    SchemaFamily,
    SeverityLabel,
    TriageDecision,
)
from finding_processor.notifications import build_notification, normalized_product, publish_notification


def sample(**changes: object) -> NormalizedFinding:
    values: dict[str, object] = {
        "schema_family": SchemaFamily.ASFF,
        "finding_id": "arn:secret/account/finding-123456789",
        "title": "title",
        "description": "sensitive description",
        "severity_label": SeverityLabel.HIGH,
        "account_id": "123456789012",
        "region": "us-east-1",
        "source_product": "Amazon GuardDuty",
        "event_time": datetime.now(UTC),
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "workflow_status": "NEW",
        "resource_type": "AwsEc2Instance",
        "resource_identifier": "i-example",
        "is_synthetic": True,
    }
    values.update(changes)
    return NormalizedFinding.model_validate(values)


def test_minimal_deterministic_message() -> None:
    decision = TriageDecision(decision=DecisionType.ESCALATE, reason_code="TEST")
    first = build_notification(sample(), decision)
    assert first == build_notification(sample(), decision)
    payload = json.loads(first)
    assert payload["account"] == "********9012"
    assert "description" not in payload and "resource_identifier" not in payload
    assert payload["recommended_next_action"] == "manual review"


def test_product_allowlist() -> None:
    assert normalized_product("Amazon Inspector") == "INSPECTOR"
    assert normalized_product("AWS Security Hub CSPM") == "SECURITY_HUB_CSPM"
    assert normalized_product("attacker-controlled") == "OTHER"


def test_key_update_and_missing_fields() -> None:
    first = idempotency_key(sample())
    assert first == idempotency_key(sample())
    assert first != idempotency_key(sample(workflow_status="NOTIFIED"))
    assert idempotency_key(sample(updated_at=None, workflow_status=None))


def test_local_first_duplicate_and_updated() -> None:
    gate = LocalIdempotency()
    calls: list[int] = []

    def operation() -> dict[str, str]:
        calls.append(1)
        return {"decision": "ESCALATE"}

    assert gate.run("one", operation)[1] is False
    assert gate.run("one", operation)[1] is True
    assert gate.run("two", operation)[1] is False
    assert len(calls) == 2


class BrokenSNS:
    def publish(self, **kwargs: object) -> dict:
        raise RuntimeError("raw provider detail")


def test_sns_failure_translated() -> None:
    with pytest.raises(NotificationError, match="sns_publish_failed"):
        publish_notification(BrokenSNS(), "arn:topic", "safe")


def test_sns_publish_with_botocore_stubber() -> None:
    client = boto3.client("sns", region_name="us-east-1")
    expected = {
        "TopicArn": "arn:aws:sns:us-east-1:111122223333:example",
        "Subject": "Security finding requires manual review",
        "Message": "safe",
    }
    with Stubber(client) as stubber:
        stubber.add_response("publish", {"MessageId": "synthetic-message-id"}, expected)
        publish_notification(client, expected["TopicArn"], expected["Message"])
