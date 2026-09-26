#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Read-only post-deployment verification helper."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import boto3


def require(condition: bool, message: str) -> None:
    """Raise a stable verification error without including provider payloads."""
    if not condition:
        raise RuntimeError(message)


def statements(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return IAM statements with a consistent list shape."""
    value = document.get("Statement", [])
    return value if isinstance(value, list) else [value]


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only verification; performs no mutations")
    parser.add_argument("--function-name", required=True)
    parser.add_argument("--table-name", required=True)
    parser.add_argument("--topic-arn", required=True)
    parser.add_argument("--rule-name", required=True)
    parser.add_argument("--dlq-url", required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--schema-mode", choices=("ocsf", "asff", "dual"), default="ocsf")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--lambda-timeout", type=int, default=30)
    parser.add_argument("--log-retention-days", type=int, default=30)
    parser.add_argument("--event-maximum-age", type=int, default=3600)
    parser.add_argument("--event-retry-attempts", type=int, default=10)
    parser.add_argument("--idempotency-expiry-seconds", type=int, default=86400)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--sns-kms-key-id", default="alias/aws/sns")
    parser.add_argument("--expect-no-subscriptions", action="store_true")
    parser.add_argument("--expect-idempotency-record", action="store_true")
    args = parser.parse_args()

    session = boto3.Session(region_name=args.region)
    lambda_client = session.client("lambda")
    dynamodb = session.client("dynamodb")
    sns = session.client("sns")
    events = session.client("events")
    sqs = session.client("sqs")
    logs = session.client("logs")
    cloudwatch = session.client("cloudwatch")
    iam = session.client("iam")

    lambda_cfg = lambda_client.get_function_configuration(FunctionName=args.function_name)
    require(lambda_cfg.get("State") == "Active", "Lambda is not active")
    require(lambda_cfg.get("Runtime") == "python3.13", "unexpected Lambda runtime")
    require(lambda_cfg.get("Architectures") == ["arm64"], "unexpected Lambda architecture")
    require(lambda_cfg.get("Timeout") == args.lambda_timeout, "unexpected Lambda timeout")
    environment = lambda_cfg.get("Environment", {}).get("Variables", {})
    expected_environment = {
        "FINDING_SCHEMA_MODE": args.schema_mode,
        "IDEMPOTENCY_TABLE": args.table_name,
        "NOTIFICATION_TOPIC_ARN": args.topic_arn,
        "IDEMPOTENCY_EXPIRY_SECONDS": str(args.idempotency_expiry_seconds),
        "POWERTOOLS_LOG_LEVEL": args.log_level,
        "POWERTOOLS_METRICS_NAMESPACE": "SecurityHubWorkflow",
        "POWERTOOLS_SERVICE_NAME": "finding-processor",
        "TRIAGE_POLICY_PATH": "config/triage-policy.json",
    }
    require(
        all(environment.get(key) == value for key, value in expected_environment.items()),
        "Lambda environment does not match the reviewed configuration",
    )
    if args.package:
        digest = hashlib.sha256(args.package.read_bytes()).digest()
        require(
            lambda_cfg.get("CodeSha256") == base64.b64encode(digest).decode("ascii"),
            "deployed Lambda package checksum does not match",
        )

    table = dynamodb.describe_table(TableName=args.table_name)["Table"]
    require(table.get("TableStatus") == "ACTIVE", "DynamoDB table is not active")
    require(
        table.get("BillingModeSummary", {}).get("BillingMode") == "PAY_PER_REQUEST",
        "DynamoDB table is not on-demand",
    )
    require(
        table.get("SSEDescription", {}).get("Status") == "ENABLED",
        "DynamoDB encryption is not enabled",
    )
    ttl = dynamodb.describe_time_to_live(TableName=args.table_name)["TimeToLiveDescription"]
    require(ttl.get("AttributeName") == "expiration", "unexpected DynamoDB TTL attribute")
    require(ttl.get("TimeToLiveStatus") in {"ENABLED", "ENABLING"}, "DynamoDB TTL is disabled")
    backups = dynamodb.describe_continuous_backups(TableName=args.table_name)
    pitr = backups["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]
    require(pitr.get("PointInTimeRecoveryStatus") == "DISABLED", "DynamoDB PITR is enabled")
    if args.expect_idempotency_record:
        count = dynamodb.scan(TableName=args.table_name, Select="COUNT", ConsistentRead=True)["Count"]
        require(count > 0, "expected idempotency record is absent")

    topic = sns.get_topic_attributes(TopicArn=args.topic_arn)["Attributes"]
    require(topic.get("KmsMasterKeyId") == args.sns_kms_key_id, "unexpected SNS encryption key")
    if args.expect_no_subscriptions:
        require(topic.get("SubscriptionsConfirmed") == "0", "unexpected SNS subscription exists")

    rule = events.describe_rule(Name=args.rule_name)
    require(rule.get("State") == "ENABLED", "EventBridge rule is disabled")
    pattern = json.loads(rule["EventPattern"])
    expected_types = {
        "ocsf": {"Findings Imported V2"},
        "asff": {"Security Hub Findings - Imported"},
        "dual": {"Findings Imported V2", "Security Hub Findings - Imported"},
    }
    detail_types = pattern.get("detail-type", [])
    require(pattern.get("source") == ["aws.securityhub"], "unexpected EventBridge source")
    require(
        isinstance(detail_types, list)
        and len(detail_types) == 1
        and detail_types[0] in expected_types[args.schema_mode],
        "unexpected EventBridge event type",
    )
    targets = events.list_targets_by_rule(Rule=args.rule_name)["Targets"]
    require(len(targets) == 1, "EventBridge rule must have exactly one target")
    target = targets[0]
    require(target.get("Arn") == lambda_cfg.get("FunctionArn"), "unexpected EventBridge target")
    require(
        target.get("RetryPolicy", {}).get("MaximumEventAgeInSeconds") == args.event_maximum_age,
        "bad event age",
    )
    require(
        target.get("RetryPolicy", {}).get("MaximumRetryAttempts") == args.event_retry_attempts,
        "bad retry count",
    )

    queue = sqs.get_queue_attributes(QueueUrl=args.dlq_url, AttributeNames=["All"])["Attributes"]
    require(queue.get("SqsManagedSseEnabled") == "true", "SQS managed encryption is disabled")
    require(queue.get("ApproximateNumberOfMessages") == "0", "EventBridge DLQ is not empty")
    require(target.get("DeadLetterConfig", {}).get("Arn") == queue.get("QueueArn"), "bad DLQ target")
    queue_policy = json.loads(queue["Policy"])
    queue_statements = statements(queue_policy)
    require(len(queue_statements) == 1, "unexpected SQS queue policy statement count")
    queue_statement = queue_statements[0]
    require(queue_statement.get("Principal") == {"Service": "events.amazonaws.com"}, "bad DLQ principal")
    require(queue_statement.get("Action") == "sqs:SendMessage", "bad DLQ action")
    source_arns = queue_statement.get("Condition", {}).get("ArnEquals", {}).get("aws:SourceArn", [])
    source_arns = source_arns if isinstance(source_arns, list) else [source_arns]
    require(rule.get("Arn") in source_arns, "DLQ policy is not restricted to the rule")

    function_policy = json.loads(lambda_client.get_policy(FunctionName=args.function_name)["Policy"])
    invoke_statements = statements(function_policy)
    require(len(invoke_statements) == 1, "unexpected Lambda resource-policy statement count")
    invoke = invoke_statements[0]
    require(invoke.get("Principal") == {"Service": "events.amazonaws.com"}, "bad Lambda principal")
    require(invoke.get("Action") == "lambda:InvokeFunction", "bad Lambda invoke action")
    require(
        invoke.get("Condition", {}).get("ArnLike", {}).get("AWS:SourceArn") == rule.get("Arn"),
        "Lambda permission is not restricted to the rule",
    )

    role_name = lambda_cfg["Role"].rsplit("/", maxsplit=1)[-1]
    role_policy = iam.get_role_policy(RoleName=role_name, PolicyName=role_name)["PolicyDocument"]
    for statement in statements(role_policy):
        actions = statement.get("Action", [])
        actions = actions if isinstance(actions, list) else [actions]
        resources = statement.get("Resource", [])
        resources = resources if isinstance(resources, list) else [resources]
        require(all("*" not in action for action in actions), "wildcard IAM action detected")
        require("*" not in resources, "wildcard IAM resource detected")

    log_groups = logs.describe_log_groups(logGroupNamePrefix=f"/aws/lambda/{args.function_name}", limit=1)[
        "logGroups"
    ]
    expected_log_group = f"/aws/lambda/{args.function_name}"
    require(
        len(log_groups) == 1 and log_groups[0].get("logGroupName") == expected_log_group,
        "Lambda log group is absent",
    )
    require(
        log_groups[0].get("retentionInDays") == args.log_retention_days,
        "unexpected log retention",
    )

    resource_prefix = args.function_name.removesuffix("-processor")
    expected_alarms = {
        f"{resource_prefix}-lambda-errors",
        f"{resource_prefix}-lambda-throttles",
        f"{resource_prefix}-dlq-visible",
        f"{resource_prefix}-notification-failures",
    }
    alarms = cloudwatch.describe_alarms(AlarmNamePrefix=f"{resource_prefix}-")
    actual_alarms = {alarm["AlarmName"] for alarm in alarms["MetricAlarms"]}
    require(expected_alarms <= actual_alarms, "one or more required alarms are absent")

    print(
        json.dumps(
            {
                "alarms": "verified",
                "dlq": "empty_and_restricted",
                "dynamodb": "active_encrypted_ttl_enabled_pitr_disabled",
                "eventbridge": "enabled_single_restricted_target",
                "iam": "no_wildcard_actions_or_resources",
                "lambda": "active_python3.13_arm64_package_verified",
                "logs": "retention_verified",
                "sns": "encryption_verified",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
