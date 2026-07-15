# SPDX-License-Identifier: MIT-0
"""Validated environment configuration."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finding_processor.exceptions import ConfigurationError


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    finding_schema_mode: str = "ocsf"
    idempotency_table: str | None = None
    idempotency_expiry_seconds: int = Field(default=86400, ge=60, le=2592000)
    notification_topic_arn: str | None = None
    policy_path: str = "config/triage-policy.json"
    local_demo: bool = False

    @field_validator("finding_schema_mode")
    @classmethod
    def schema_mode(cls, value: str) -> str:
        if value not in {"ocsf", "asff", "dual"}:
            raise ValueError("invalid finding schema mode")
        return value


def load_settings() -> Settings:
    try:
        return Settings(
            finding_schema_mode=os.getenv("FINDING_SCHEMA_MODE", "ocsf").lower(),
            idempotency_table=os.getenv("IDEMPOTENCY_TABLE") or None,
            idempotency_expiry_seconds=int(os.getenv("IDEMPOTENCY_EXPIRY_SECONDS", "86400")),
            notification_topic_arn=os.getenv("NOTIFICATION_TOPIC_ARN") or None,
            policy_path=os.getenv(
                "TRIAGE_POLICY_PATH", str(Path(__file__).parents[2] / "config/triage-policy.json")
            ),
            local_demo=os.getenv("LOCAL_DEMO", "false").lower() == "true",
        )
    except (ValueError, TypeError) as exc:
        raise ConfigurationError("invalid_runtime_configuration") from exc
