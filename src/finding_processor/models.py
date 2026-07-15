# SPDX-License-Identifier: MIT-0
"""Schema-independent domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SchemaFamily(StrEnum):
    OCSF = "OCSF"
    ASFF = "ASFF"


class SeverityLabel(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class DecisionType(StrEnum):
    ESCALATE = "ESCALATE"
    RECORD = "RECORD"
    IGNORE = "IGNORE"
    REJECT = "REJECT"
    DUPLICATE = "DUPLICATE"


class NormalizedFinding(BaseModel):
    """Small normalized representation used by workflow logic."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_family: SchemaFamily
    schema_version: str | None = None
    finding_id: str = Field(min_length=1, max_length=512)
    source_product: str = Field(default="UNKNOWN", max_length=80)
    account_id: str | None = Field(default=None, max_length=64)
    region: str | None = Field(default=None, max_length=32)
    title: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=4096)
    severity_label: SeverityLabel
    severity_score: float | None = Field(default=None, ge=0, le=100)
    record_state: str | None = Field(default=None, max_length=32)
    workflow_status: str | None = Field(default=None, max_length=32)
    resource_type: str | None = Field(default=None, max_length=128)
    resource_identifier: str | None = Field(default=None, max_length=512)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    event_time: datetime
    is_sample: bool = False
    is_synthetic: bool = False

    @field_validator("record_state", "workflow_status", mode="before")
    @classmethod
    def upper_optional(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class TriageDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision: DecisionType
    reason_code: str = Field(pattern=r"^[A-Z0-9_]+$", max_length=64)
