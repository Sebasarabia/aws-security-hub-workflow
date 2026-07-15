#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Read-only post-deployment verification helper."""

from __future__ import annotations

import argparse

import boto3


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only verification; performs no mutations")
    parser.add_argument("--function-name", required=True)
    parser.add_argument("--table-name", required=True)
    parser.add_argument("--topic-arn", required=True)
    args = parser.parse_args()
    lambda_cfg = boto3.client("lambda").get_function_configuration(FunctionName=args.function_name)
    table = boto3.client("dynamodb").describe_table(TableName=args.table_name)["Table"]
    topic = boto3.client("sns").get_topic_attributes(TopicArn=args.topic_arn)["Attributes"]
    print(
        {
            "lambda_state": lambda_cfg.get("State"),
            "table_status": table.get("TableStatus"),
            "topic": topic.get("TopicArn"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
