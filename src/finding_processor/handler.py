# SPDX-License-Identifier: MIT-0
"""AWS Lambda entry point. Raw input is never logged."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import boto3
from aws_lambda_powertools.metrics import MetricUnit

from finding_processor.adapters import adapt_event
from finding_processor.config import Settings, load_settings
from finding_processor.exceptions import FindingProcessorError, FindingValidationError
from finding_processor.idempotency import LocalIdempotency, idempotency_key, run_with_powertools
from finding_processor.models import DecisionType
from finding_processor.notifications import build_notification, normalized_product, publish_notification
from finding_processor.observability import logger, metric, metrics
from finding_processor.sanitization import mask_account_id
from finding_processor.triage import evaluate, load_policy

_sns = boto3.client("sns")
_dynamodb = boto3.client("dynamodb")
_local_idempotency = LocalIdempotency()


def _allowed_family(mode: str, detail_type: object) -> bool:
    family = (
        "ocsf"
        if detail_type == "Findings Imported V2"
        else "asff"
        if detail_type == "Security Hub Findings - Imported"
        else "unknown"
    )
    return mode == "dual" or mode == family


def process_event(
    event: Mapping[str, Any],
    *,
    settings: Settings,
    sns_client: Any = None,
    lambda_context: Any = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    event_id = str(event.get("id", "UNKNOWN"))[:64]
    logger.append_keys(correlation_id=event_id)
    metric("FindingsReceived")
    if not _allowed_family(settings.finding_schema_mode, event.get("detail-type")):
        metric("FindingsRejected")
        return {"decision": "REJECT", "reason_code": "SCHEMA_MODE_REJECTED"}
    try:
        finding = adapt_event(event)
        metric("FindingsValidated")
        policy = load_policy(settings.policy_path)
        decision = evaluate(finding, policy)
        result = {"decision": decision.decision.value, "reason_code": decision.reason_code}

        def side_effect() -> dict[str, Any]:
            if decision.decision is DecisionType.ESCALATE:
                if not settings.notification_topic_arn:
                    raise FindingProcessorError("notification_topic_not_configured")
                publish_notification(
                    sns_client or _sns, settings.notification_topic_arn, build_notification(finding, decision)
                )
            return result

        key = idempotency_key(finding)
        if settings.local_demo:
            result, duplicate = _local_idempotency.run(key, side_effect)
        else:
            if not settings.idempotency_table:
                raise FindingProcessorError("idempotency_table_not_configured")
            result, duplicate = run_with_powertools(
                table_name=settings.idempotency_table,
                expiry_seconds=settings.idempotency_expiry_seconds,
                key=key,
                operation=side_effect,
                dynamodb_client=_dynamodb,
                lambda_context=lambda_context,
            )
        if duplicate:
            metric("DuplicateFindings")
        else:
            metric(
                {
                    "ESCALATE": "FindingsEscalated",
                    "RECORD": "FindingsRecorded",
                    "IGNORE": "FindingsIgnored",
                    "REJECT": "FindingsRejected",
                }[result["decision"]]
            )
        logger.info(
            "finding_decision",
            extra={
                "schema_family": finding.schema_family.value,
                "decision": result["decision"],
                "reason_code": result["reason_code"],
                "account": mask_account_id(finding.account_id),
                "source_product": normalized_product(finding.source_product),
            },
        )
        return result
    except FindingValidationError as exc:
        metric("FindingsRejected")
        logger.warning("finding_rejected", extra={"reason_code": str(exc)})
        return {"decision": "REJECT", "reason_code": str(exc).upper()}
    except Exception as exc:
        metric("ProcessingErrors")
        if "sns" in str(exc).lower() or "notification" in str(exc).lower():
            metric("NotificationFailures")
        # Do not serialize exception text or a traceback: provider errors can contain
        # untrusted finding fragments. The stable class name is sufficient for routing.
        logger.error("processing_failed", extra={"reason_code": type(exc).__name__})
        raise
    finally:
        metric("ProcessingLatency", (time.perf_counter() - started) * 1000, MetricUnit.Milliseconds)


@logger.inject_lambda_context(clear_state=True, log_event=False)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return process_event(event, settings=load_settings(), lambda_context=context)
