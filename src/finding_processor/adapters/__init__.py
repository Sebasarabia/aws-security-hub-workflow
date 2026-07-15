# SPDX-License-Identifier: MIT-0
"""Schema adapter dispatch."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from finding_processor.adapters.asff import adapt_asff
from finding_processor.adapters.ocsf import adapt_ocsf
from finding_processor.exceptions import FindingValidationError
from finding_processor.models import NormalizedFinding

OCSF_DETAIL_TYPE = "Findings Imported V2"
ASFF_DETAIL_TYPE = "Security Hub Findings - Imported"


def adapt_event(event: Mapping[str, Any]) -> NormalizedFinding:
    required = ("version", "id", "detail-type", "source", "time", "region", "detail")
    if any(key not in event for key in required):
        raise FindingValidationError("event_envelope_missing_required_field")
    if event.get("version") != "0" or event.get("source") != "aws.securityhub":
        raise FindingValidationError("event_envelope_not_supported")
    detail = event.get("detail")
    if not isinstance(detail, Mapping):
        raise FindingValidationError("event_detail_not_object")
    findings = detail.get("findings")
    if not isinstance(findings, list) or len(findings) != 1:
        raise FindingValidationError("event_must_contain_exactly_one_finding")
    finding = findings[0]
    if not isinstance(finding, Mapping):
        raise FindingValidationError("finding_not_object")
    event_time = event.get("time")
    region = event.get("region")
    detail_type = event.get("detail-type")
    if detail_type == OCSF_DETAIL_TYPE:
        return adapt_ocsf(finding, event_time=event_time, event_region=region)
    if detail_type == ASFF_DETAIL_TYPE:
        return adapt_asff(finding, event_time=event_time, event_region=region)
    raise FindingValidationError("unknown_event_family")
