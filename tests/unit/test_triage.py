# SPDX-License-Identifier: MIT-0
"""Policy decisions remain simple and explainable."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from finding_processor.models import DecisionType, NormalizedFinding, SchemaFamily, SeverityLabel
from finding_processor.triage import TriagePolicy, evaluate, load_policy

ROOT = Path(__file__).parents[2]


def finding(severity: SeverityLabel, **changes: object) -> NormalizedFinding:
    values: dict[str, object] = {
        "schema_family": SchemaFamily.OCSF,
        "finding_id": "test",
        "title": "Synthetic test",
        "severity_label": severity,
        "record_state": "ACTIVE",
        "workflow_status": "NEW",
        "event_time": datetime.now(UTC),
    }
    values.update(changes)
    return NormalizedFinding.model_validate(values)


@pytest.mark.parametrize(
    ("severity", "decision"),
    [
        (SeverityLabel.CRITICAL, DecisionType.ESCALATE),
        (SeverityLabel.HIGH, DecisionType.ESCALATE),
        (SeverityLabel.MEDIUM, DecisionType.RECORD),
        (SeverityLabel.LOW, DecisionType.IGNORE),
        (SeverityLabel.INFORMATIONAL, DecisionType.IGNORE),
        (SeverityLabel.UNKNOWN, DecisionType.REJECT),
    ],
)
def test_severity_decisions(severity: SeverityLabel, decision: DecisionType) -> None:
    assert evaluate(finding(severity), load_policy(ROOT / "config/triage-policy.json")).decision is decision


@pytest.mark.parametrize("status", ["RESOLVED", "SUPPRESSED"])
def test_workflow_ignored(status: str) -> None:
    result = evaluate(
        finding(SeverityLabel.CRITICAL, workflow_status=status),
        load_policy(ROOT / "config/triage-policy.json"),
    )
    assert result.reason_code == "IGNORED_WORKFLOW_STATUS"


def test_inactive_ignored_and_unsupported_policy() -> None:
    policy = load_policy(ROOT / "config/triage-policy.json")
    assert (
        evaluate(finding(SeverityLabel.CRITICAL, record_state="ARCHIVED"), policy).reason_code
        == "INACTIVE_RECORD_STATE"
    )
    with pytest.raises(ValidationError):
        TriagePolicy.model_validate(
            {
                "schema_version": "2.0",
                "escalate_severities": [],
                "record_severities": [],
                "ignore_severities": [],
                "ignored_workflow_statuses": [],
            }
        )
