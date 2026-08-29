# SPDX-License-Identifier: MIT-0
"""Low-cardinality structured observability using Embedded Metric Format."""

from __future__ import annotations

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger(service="finding-processor", utc=True, use_rfc3339=True)
metrics = Metrics(namespace="SecurityHubWorkflow", service="finding-processor")


def metric(name: str, value: float = 1, unit: MetricUnit = MetricUnit.Count) -> bool:
    """Emit a metric without making observability failure change the workflow decision."""
    try:
        metrics.add_metric(name=name, unit=unit, value=value)
    except Exception:  # Metrics are non-critical; never expose provider exception content.
        logger.warning("metric_emission_failed", extra={"metric_name": name})
        return False
    return True
