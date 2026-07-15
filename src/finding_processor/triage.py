# SPDX-License-Identifier: MIT-0
"""Explainable, policy-driven triage."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from finding_processor.exceptions import ConfigurationError
from finding_processor.models import DecisionType, NormalizedFinding, SeverityLabel, TriageDecision


class TriagePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str
    escalate_severities: frozenset[SeverityLabel]
    record_severities: frozenset[SeverityLabel]
    ignore_severities: frozenset[SeverityLabel]
    ignored_workflow_statuses: frozenset[str]
    require_active_record_state: bool = True

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported policy schema version")
        return value


def load_policy(path: str | Path) -> TriagePolicy:
    try:
        return TriagePolicy.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError("invalid_triage_policy") from exc


def evaluate(finding: NormalizedFinding, policy: TriagePolicy) -> TriageDecision:
    if finding.workflow_status and finding.workflow_status.upper() in policy.ignored_workflow_statuses:
        return TriageDecision(decision=DecisionType.IGNORE, reason_code="IGNORED_WORKFLOW_STATUS")
    if (
        policy.require_active_record_state
        and finding.record_state
        and finding.record_state.upper() not in {"ACTIVE", "NEW", "IN_PROGRESS"}
    ):
        return TriageDecision(decision=DecisionType.IGNORE, reason_code="INACTIVE_RECORD_STATE")
    if finding.severity_label in policy.escalate_severities:
        return TriageDecision(decision=DecisionType.ESCALATE, reason_code="POLICY_SEVERITY_ESCALATION")
    if finding.severity_label in policy.record_severities:
        return TriageDecision(decision=DecisionType.RECORD, reason_code="POLICY_SEVERITY_RECORD")
    if finding.severity_label in policy.ignore_severities:
        return TriageDecision(decision=DecisionType.IGNORE, reason_code="POLICY_SEVERITY_IGNORE")
    return TriageDecision(decision=DecisionType.REJECT, reason_code="UNSUPPORTED_SEVERITY")
