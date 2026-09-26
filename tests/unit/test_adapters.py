# SPDX-License-Identifier: MIT-0
"""Adapter and envelope behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finding_processor.adapters import adapt_event
from finding_processor.exceptions import FindingValidationError
from finding_processor.models import SchemaFamily, SeverityLabel

ROOT = Path(__file__).parents[2]


def fixture(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_valid_ocsf() -> None:
    result = adapt_event(fixture("fixtures/ocsf/high-severity.json"))
    assert result.schema_family is SchemaFamily.OCSF
    assert result.severity_label is SeverityLabel.HIGH
    assert result.is_synthetic is True
    assert result.account_id == "000000000000"


def test_valid_asff() -> None:
    result = adapt_event(fixture("fixtures/asff/high-severity.json"))
    assert result.schema_family is SchemaFamily.ASFF
    assert result.severity_label is SeverityLabel.HIGH
    assert result.is_synthetic is True


@pytest.mark.parametrize("field", ["id", "source", "account", "time", "detail", "region"])
def test_missing_envelope_field(field: str) -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    del event[field]
    with pytest.raises(FindingValidationError, match="envelope_missing"):
        adapt_event(event)


@pytest.mark.parametrize(
    ("field", "value"),
    [("id", ""), ("detail-type", 1), ("account", "not-an-account"), ("time", None), ("region", [])],
)
def test_invalid_envelope_scalar(field: str, value: object) -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    event[field] = value
    with pytest.raises(FindingValidationError, match="envelope_invalid_field"):
        adapt_event(event)


@pytest.mark.parametrize("findings", [[], [{}, {}], "bad", ["bad"]])
def test_invalid_finding_collection(findings: object) -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    event["detail"]["findings"] = findings
    with pytest.raises(FindingValidationError):
        adapt_event(event)


def test_unknown_family_and_source() -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    event["detail-type"] = "Other"
    with pytest.raises(FindingValidationError, match="unknown_event_family"):
        adapt_event(event)
    event["source"] = "example.synthetic"
    with pytest.raises(FindingValidationError, match="not_supported"):
        adapt_event(event)


@pytest.mark.parametrize("family,id_field", [("ocsf", "uid"), ("asff", "Id")])
def test_missing_finding_id(family: str, id_field: str) -> None:
    event = fixture(f"fixtures/{family}/high-severity.json")
    finding = event["detail"]["findings"][0]
    if family == "ocsf":
        del finding["finding_info"][id_field]
    else:
        del finding[id_field]
    with pytest.raises(FindingValidationError, match="missing_finding_id"):
        adapt_event(event)


def test_asff_missing_and_invalid_timestamps() -> None:
    event = fixture("fixtures/asff/high-severity.json")
    del event["detail"]["findings"][0]["UpdatedAt"]
    with pytest.raises(FindingValidationError, match="missing_timestamp"):
        adapt_event(event)
    event = fixture("fixtures/asff/high-severity.json")
    event["detail"]["findings"][0]["CreatedAt"] = "not-time"
    with pytest.raises(FindingValidationError, match="invalid_asff_created_time"):
        adapt_event(event)


def test_unknown_severity_and_oversized_text_are_safe() -> None:
    event = fixture("fixtures/asff/high-severity.json")
    finding = event["detail"]["findings"][0]
    finding["Severity"]["Label"] = "IMPOSSIBLE"
    finding["Title"] = "x" * 10000
    finding["Description"] = "y" * 10000
    result = adapt_event(event)
    assert result.severity_label is SeverityLabel.UNKNOWN
    assert len(result.title) == 512
    assert len(result.description or "") == 4096


def test_ocsf_numeric_timestamp_and_severity() -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    finding = event["detail"]["findings"][0]
    finding.pop("severity")
    finding["severity_id"] = 5
    finding["finding_info"]["modified_time_dt"] = None
    finding["time"] = 1783944000000
    result = adapt_event(event)
    assert result.severity_label is SeverityLabel.CRITICAL
    assert result.updated_at is not None


def test_ocsf_invalid_optional_shapes_and_values() -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    finding = event["detail"]["findings"][0]
    finding["severity"] = "not-known"
    finding["severity_id"] = "not-a-number"
    finding["metadata"]["product"] = "not-an-object"
    finding["resources"] = []
    result = adapt_event(event)
    assert result.severity_label is SeverityLabel.UNKNOWN
    assert result.resource_identifier is None

    finding["finding_info"]["created_time_dt"] = "invalid"
    with pytest.raises(FindingValidationError, match="invalid_ocsf_created_time"):
        adapt_event(event)


def test_ocsf_missing_title_and_event_time() -> None:
    event = fixture("fixtures/ocsf/high-severity.json")
    del event["detail"]["findings"][0]["finding_info"]["title"]
    with pytest.raises(FindingValidationError, match="missing_title"):
        adapt_event(event)

    event = fixture("fixtures/ocsf/high-severity.json")
    event["time"] = None
    with pytest.raises(FindingValidationError, match="envelope_invalid_field"):
        adapt_event(event)
