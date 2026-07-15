# SPDX-License-Identifier: MIT-0
"""Low-cardinality structured observability using Embedded Metric Format."""

from __future__ import annotations

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger(service="finding-processor", utc=True, use_rfc3339=True)
metrics = Metrics(namespace="SecurityHubWorkflow", service="finding-processor")


def metric(name: str, value: float = 1, unit: MetricUnit = MetricUnit.Count) -> None:
    metrics.add_metric(name=name, unit=unit, value=value)
