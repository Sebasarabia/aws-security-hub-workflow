# SPDX-License-Identifier: MIT-0
"""Minimal deterministic SNS notification construction."""

from __future__ import annotations

import json
from typing import Any, Protocol

from finding_processor.exceptions import NotificationError
from finding_processor.models import NormalizedFinding, TriageDecision
from finding_processor.sanitization import mask_account_id, sanitize_text, shorten_identifier


def normalized_product(value: str) -> str:
    name = sanitize_text(value, max_length=80).upper()
    for allowed in (
        "GUARDDUTY",
        "INSPECTOR",
        "MACIE",
        "SECURITY HUB CSPM",
        "SECURITY HUB",
        "IAM ACCESS ANALYZER",
    ):
        if allowed in name:
            return allowed.replace(" ", "_")
    return "OTHER"


def build_notification(finding: NormalizedFinding, decision: TriageDecision) -> str:
    payload = {
        "decision": decision.decision.value,
        "reason_code": decision.reason_code,
        "severity": finding.severity_label.value,
        "source_product": normalized_product(finding.source_product),
        "region": finding.region or "UNKNOWN",
        "resource_type": finding.resource_type or "UNKNOWN",
        "account": mask_account_id(finding.account_id),
        "finding": shorten_identifier(finding.finding_id),
        "sample_or_synthetic": finding.is_sample or finding.is_synthetic,
        "recommended_next_action": "manual review",
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SNSClient(Protocol):
    def publish(self, **kwargs: Any) -> dict[str, Any]: ...


def publish_notification(client: SNSClient, topic_arn: str, message: str) -> None:
    try:
        client.publish(TopicArn=topic_arn, Subject="Security finding requires manual review", Message=message)
    except Exception as exc:
        raise NotificationError("sns_publish_failed") from exc
