# SPDX-License-Identifier: MIT-0
"""Powertools-backed idempotency helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

from finding_processor.models import NormalizedFinding


def idempotency_key(finding: NormalizedFinding) -> str:
    updated = finding.updated_at.isoformat() if finding.updated_at else "NO_UPDATED_AT"
    workflow = finding.workflow_status or "NO_WORKFLOW_STATUS"
    raw = "|".join((finding.schema_family.value, finding.finding_id, updated, workflow))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_with_powertools(
    *,
    table_name: str,
    expiry_seconds: int,
    key: str,
    operation: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """Execute one operation using Powertools' concurrency-safe DynamoDB records."""
    from aws_lambda_powertools.utilities.idempotency import (  # lazy for local demo
        DynamoDBPersistenceLayer,
        IdempotencyConfig,
        idempotent_function,
    )
    from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import DataRecord

    persistence = DynamoDBPersistenceLayer(table_name=table_name)

    def duplicate_response(response: Any, idempotent_data: DataRecord) -> dict[str, str]:
        del response, idempotent_data
        return {"decision": "DUPLICATE", "reason_code": "IDEMPOTENCY_RECORD_EXISTS"}

    config = IdempotencyConfig(
        expires_after_seconds=expiry_seconds,
        use_local_cache=True,
        response_hook=duplicate_response,
    )

    @idempotent_function(  # type: ignore[misc]
        data_keyword_argument="payload",
        persistence_store=persistence,
        config=config,
    )
    def protected(*, payload: dict[str, str]) -> dict[str, Any]:
        return operation()

    result = protected(payload={"idempotency_key": key})
    return result, result.get("decision") == "DUPLICATE"


class LocalIdempotency:
    """Deterministic process-local test double, never used in Lambda."""

    def __init__(self) -> None:
        self._keys: set[str] = set()

    def run(self, key: str, operation: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], bool]:
        if key in self._keys:
            return {"decision": "DUPLICATE", "reason_code": "IDEMPOTENCY_RECORD_EXISTS"}, True
        result = operation()
        self._keys.add(key)
        return result, False
