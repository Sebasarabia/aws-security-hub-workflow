# SPDX-License-Identifier: MIT-0
"""ASFF adapter for Security Hub CSPM compatibility."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from finding_processor.exceptions import FindingValidationError
from finding_processor.models import NormalizedFinding, SchemaFamily, SeverityLabel
from finding_processor.sanitization import sanitize_resource_identifier, sanitize_text


def _parse_time(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise FindingValidationError(f"invalid_{field}") from exc


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _is_true(value: object) -> bool:
    return value is True or (isinstance(value, str) and value.casefold() == "true")


def adapt_asff(finding: Mapping[str, Any], *, event_time: object, event_region: object) -> NormalizedFinding:
    finding_id = sanitize_text(finding.get("Id"), max_length=512)
    title = sanitize_text(finding.get("Title"), max_length=512)
    if not finding_id:
        raise FindingValidationError("asff_missing_finding_id")
    if not title:
        raise FindingValidationError("asff_missing_title")
    severity_obj = _mapping(finding.get("Severity"))
    label = sanitize_text(severity_obj.get("Label"), max_length=32).upper()
    aliases = {"INFO": "INFORMATIONAL"}
    label = aliases.get(label, label)
    severity = SeverityLabel(label) if label in SeverityLabel._value2member_map_ else SeverityLabel.UNKNOWN
    score_raw = severity_obj.get("Normalized")
    score = float(score_raw) if isinstance(score_raw, int | float) else None
    workflow = _mapping(finding.get("Workflow"))
    product = _mapping(finding.get("ProductFields"))
    resources = finding.get("Resources")
    resource = (
        resources[0]
        if isinstance(resources, list) and resources and isinstance(resources[0], Mapping)
        else {}
    )
    parsed_event_time = _parse_time(event_time, "event_time")
    if parsed_event_time is None:
        raise FindingValidationError("missing_event_time")
    created = _parse_time(finding.get("CreatedAt"), "asff_created_time")
    updated = _parse_time(finding.get("UpdatedAt"), "asff_updated_time")
    if created is None or updated is None:
        raise FindingValidationError("asff_missing_timestamp")
    return NormalizedFinding(
        schema_family=SchemaFamily.ASFF,
        schema_version=sanitize_text(finding.get("SchemaVersion"), max_length=32) or None,
        finding_id=finding_id,
        source_product=sanitize_text(
            finding.get("ProductName") or product.get("aws/securityhub/ProductName"), max_length=80
        )
        or "UNKNOWN",
        account_id=sanitize_text(finding.get("AwsAccountId"), max_length=64) or None,
        region=sanitize_text(finding.get("Region") or event_region, max_length=32) or None,
        title=title,
        description=sanitize_text(finding.get("Description"), max_length=4096) or None,
        severity_label=severity,
        severity_score=score,
        record_state=sanitize_text(finding.get("RecordState"), max_length=32) or None,
        workflow_status=sanitize_text(workflow.get("Status"), max_length=32) or None,
        resource_type=sanitize_text(resource.get("Type"), max_length=128) or None,
        resource_identifier=sanitize_resource_identifier(resource.get("Id")),
        created_at=created,
        updated_at=updated,
        event_time=parsed_event_time,
        is_sample=_is_true(finding.get("Sample")),
        is_synthetic=_is_true(product.get("aws-security-hub-workflow/synthetic")),
    )
