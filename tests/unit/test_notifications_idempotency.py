# SPDX-License-Identifier: MIT-0
"""Notification minimization and idempotency semantics."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import boto3
import pytest
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyPersistenceLayerError,
)
from botocore.stub import ANY, Stubber

from finding_processor.exceptions import NotificationError
from finding_processor.idempotency import LocalIdempotency, idempotency_key, run_with_powertools
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


class FakeLambdaContext:
    def get_remaining_time_in_millis(self) -> int:
        return 30_000


def dynamodb_client() -> object:
    return boto3.client("dynamodb", region_name="us-east-1")


def test_powertools_first_delivery_and_expiry_condition() -> None:
    client = dynamodb_client()
    with Stubber(client) as stubber:
        stubber.add_response(
            "put_item",
            {},
            {
                "TableName": "idempotency-test",
                "Item": ANY,
                "ConditionExpression": (
                    "attribute_not_exists(#id) OR #expiry < :now OR "
                    "(#status = :inprogress AND attribute_exists(#in_progress_expiry) "
                    "AND #in_progress_expiry < :now_in_millis)"
                ),
                "ExpressionAttributeNames": {
                    "#id": "id",
                    "#expiry": "expiration",
                    "#in_progress_expiry": "in_progress_expiration",
                    "#status": "status",
                },
                "ExpressionAttributeValues": {
                    ":now": ANY,
                    ":now_in_millis": ANY,
                    ":inprogress": {"S": "INPROGRESS"},
                },
                "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
            },
        )
        stubber.add_response("update_item", {})
        result, duplicate = run_with_powertools(
            table_name="idempotency-test",
            expiry_seconds=60,
            key="stable-key",
            operation=lambda: {"decision": "ESCALATE", "reason_code": "TEST"},
            dynamodb_client=client,
            lambda_context=FakeLambdaContext(),
        )
    assert result == {"decision": "ESCALATE", "reason_code": "TEST"}
    assert duplicate is False


def test_powertools_exact_duplicate() -> None:
    client = dynamodb_client()
    stored = {
        "id": {"S": "stored-key"},
        "expiration": {"N": str(int(time.time()) + 60)},
        "status": {"S": "COMPLETED"},
        "data": {"S": json.dumps({"decision": "ESCALATE", "reason_code": "TEST"})},
    }
    with Stubber(client) as stubber:
        stubber.add_client_error(
            "put_item",
            service_error_code="ConditionalCheckFailedException",
            service_message="record exists",
            http_status_code=400,
        )
        stubber.add_response("get_item", {"Item": stored})
        result, duplicate = run_with_powertools(
            table_name="idempotency-test",
            expiry_seconds=60,
            key="stable-key",
            operation=lambda: pytest.fail("duplicate must not execute the protected operation"),
            dynamodb_client=client,
            lambda_context=FakeLambdaContext(),
        )
    assert result == {"decision": "DUPLICATE", "reason_code": "IDEMPOTENCY_RECORD_EXISTS"}
    assert duplicate is True


def test_powertools_concurrent_duplicate() -> None:
    client = dynamodb_client()
    stored = {
        "id": {"S": "stored-key"},
        "expiration": {"N": str(int(time.time()) + 60)},
        "in_progress_expiration": {"N": str(int(time.time() * 1000) + 30_000)},
        "status": {"S": "INPROGRESS"},
    }
    with Stubber(client) as stubber:
        stubber.add_client_error(
            "put_item",
            service_error_code="ConditionalCheckFailedException",
            service_message="record in progress",
            http_status_code=400,
        )
        stubber.add_response("get_item", {"Item": stored})
        with pytest.raises(IdempotencyAlreadyInProgressError):
            run_with_powertools(
                table_name="idempotency-test",
                expiry_seconds=60,
                key="stable-key",
                operation=lambda: pytest.fail("concurrent duplicate must not execute"),
                dynamodb_client=client,
                lambda_context=FakeLambdaContext(),
            )


def test_powertools_dynamodb_failure() -> None:
    client = dynamodb_client()
    with Stubber(client) as stubber:
        stubber.add_client_error(
            "put_item",
            service_error_code="InternalServerError",
            service_message="untrusted provider detail",
            http_status_code=500,
        )
        with pytest.raises(IdempotencyPersistenceLayerError):
            run_with_powertools(
                table_name="idempotency-test",
                expiry_seconds=60,
                key="stable-key",
                operation=lambda: pytest.fail("failed lock must not execute"),
                dynamodb_client=client,
                lambda_context=FakeLambdaContext(),
            )


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
