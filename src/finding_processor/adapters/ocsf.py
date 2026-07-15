# SPDX-License-Identifier: MIT-0
"""OCSF 1.6 adapter for current Security Hub findings."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from finding_processor.exceptions import FindingValidationError
from finding_processor.models import NormalizedFinding, SchemaFamily, SeverityLabel
from finding_processor.sanitization import sanitize_resource_identifier, sanitize_text


def _parse_time(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        if isinstance(value, int | float):
            # OCSF epoch values are milliseconds.
            return datetime.fromtimestamp(float(value) / 1000, tz=UTC)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError) as exc:
        raise FindingValidationError(f"invalid_{field}") from exc


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _severity(finding: Mapping[str, Any]) -> tuple[SeverityLabel, float | None]:
    name = sanitize_text(finding.get("severity") or finding.get("severity_name"), max_length=32).upper()
    aliases = {"FATAL": "CRITICAL", "INFO": "INFORMATIONAL"}
    name = aliases.get(name, name)
    if name in SeverityLabel._value2member_map_:
        return SeverityLabel(name), _number(finding.get("severity_id"))
    severity_id = _number(finding.get("severity_id"))
    mapping = {
        5: SeverityLabel.CRITICAL,
        4: SeverityLabel.HIGH,
        3: SeverityLabel.MEDIUM,
        2: SeverityLabel.LOW,
        1: SeverityLabel.INFORMATIONAL,
        0: SeverityLabel.UNKNOWN,
    }
    if severity_id is not None and int(severity_id) in mapping:
        return mapping[int(severity_id)], severity_id
    return SeverityLabel.UNKNOWN, severity_id


def _number(value: object) -> float | None:
    try:
        return float(value) if isinstance(value, str | int | float) else None
    except (TypeError, ValueError):
        return None


def adapt_ocsf(finding: Mapping[str, Any], *, event_time: object, event_region: object) -> NormalizedFinding:
    metadata = _mapping(finding.get("metadata"))
    finding_info = _mapping(finding.get("finding_info"))
    finding_id = sanitize_text(
        finding_info.get("uid") or finding.get("finding_uid") or metadata.get("uid"), max_length=512
    )
    title = sanitize_text(finding_info.get("title") or finding.get("message"), max_length=512)
    if not finding_id:
        raise FindingValidationError("ocsf_missing_finding_id")
    if not title:
        raise FindingValidationError("ocsf_missing_title")
    product = _mapping(metadata.get("product"))
    cloud = _mapping(finding.get("cloud"))
    account = _mapping(cloud.get("account"))
    resources = finding.get("resources")
    resource = (
        resources[0]
        if isinstance(resources, list) and resources and isinstance(resources[0], Mapping)
        else {}
    )
    severity, score = _severity(finding)
    created = _parse_time(
        finding_info.get("created_time_dt") or finding_info.get("created_time") or finding.get("time"),
        "ocsf_created_time",
    )
    updated = _parse_time(
        finding_info.get("modified_time_dt") or finding_info.get("modified_time") or finding.get("time"),
        "ocsf_updated_time",
    )
    parsed_event_time = _parse_time(event_time, "event_time")
    if parsed_event_time is None:
        raise FindingValidationError("missing_event_time")
    return NormalizedFinding(
        schema_family=SchemaFamily.OCSF,
        schema_version=sanitize_text(metadata.get("version"), max_length=32) or "1.6",
        finding_id=finding_id,
        source_product=sanitize_text(product.get("name") or metadata.get("product_name"), max_length=80)
        or "UNKNOWN",
        account_id=sanitize_text(account.get("uid"), max_length=64) or None,
        region=sanitize_text(cloud.get("region") or event_region, max_length=32) or None,
        title=title,
        description=sanitize_text(finding_info.get("desc") or finding.get("message"), max_length=4096)
        or None,
        severity_label=severity,
        severity_score=score,
        record_state=sanitize_text(finding.get("status") or finding.get("status_code"), max_length=32)
        or "ACTIVE",
        workflow_status=sanitize_text(finding.get("status") or finding.get("status_code"), max_length=32)
        or "NEW",
        resource_type=sanitize_text(resource.get("type"), max_length=128) or None,
        resource_identifier=sanitize_resource_identifier(resource.get("uid")),
        created_at=created,
        updated_at=updated,
        event_time=parsed_event_time,
        is_sample=bool(finding.get("is_sample")),
        is_synthetic=bool(finding.get("is_synthetic")),
    )
