# SPDX-License-Identifier: MIT-0
mock_provider "aws" {
  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::000000000000:role/mock", id = "mock-role" }
  }
  mock_resource "aws_cloudwatch_log_group" {
    defaults = { arn = "arn:aws:logs:us-east-1:000000000000:log-group:mock" }
  }
  mock_resource "aws_dynamodb_table" {
    defaults = { arn = "arn:aws:dynamodb:us-east-1:000000000000:table/mock" }
  }
  mock_resource "aws_sns_topic" {
    defaults = { arn = "arn:aws:sns:us-east-1:000000000000:mock" }
  }
  mock_resource "aws_sqs_queue" {
    defaults = {
      arn = "arn:aws:sqs:us-east-1:000000000000:mock"
      id  = "https://sqs.us-east-1.amazonaws.com/000000000000/mock"
      url = "https://sqs.us-east-1.amazonaws.com/000000000000/mock"
    }
  }
  mock_resource "aws_lambda_function" {
    defaults = { arn = "arn:aws:lambda:us-east-1:000000000000:function:mock" }
  }
  mock_resource "aws_cloudwatch_event_rule" {
    defaults = { arn = "arn:aws:events:us-east-1:000000000000:rule/mock" }
  }
}

variables {
  # Mocked provider tests only require a deterministic local file for source_code_hash.
  lambda_package_path = "../config/triage-policy.json"
}

run "default_ocsf_configuration" {
  command = apply

  assert {
    condition     = var.finding_schema_mode == "ocsf"
    error_message = "OCSF must be the default schema mode."
  }
  assert {
    condition     = length(aws_cloudwatch_event_rule.findings) == 1 && contains(keys(aws_cloudwatch_event_rule.findings), "ocsf")
    error_message = "Default routing must create only the OCSF rule."
  }
  assert {
    condition     = jsondecode(aws_cloudwatch_event_rule.findings["ocsf"].event_pattern)["detail-type"][0] == "Findings Imported V2"
    error_message = "OCSF detail type is incorrect."
  }
  assert {
    condition     = aws_lambda_function.processor.runtime == "python3.13" && aws_lambda_function.processor.architectures[0] == "arm64"
    error_message = "Lambda runtime or architecture changed."
  }
  assert {
    condition     = aws_lambda_function.processor.timeout == 30
    error_message = "Lambda timeout default changed."
  }
  assert {
    condition     = aws_lambda_function.processor.environment[0].variables["FINDING_SCHEMA_MODE"] == "ocsf"
    error_message = "Lambda schema environment is incorrect."
  }
  assert {
    condition     = aws_cloudwatch_event_target.processor["ocsf"].dead_letter_config[0].arn == aws_sqs_queue.eventbridge_dlq.arn
    error_message = "EventBridge target must use the DLQ."
  }
  assert {
    condition     = aws_dynamodb_table.idempotency.billing_mode == "PAY_PER_REQUEST" && aws_dynamodb_table.idempotency.ttl[0].enabled
    error_message = "DynamoDB must use on-demand billing and TTL."
  }
  assert {
    condition     = aws_sns_topic.escalation.kms_master_key_id == "alias/aws/sns"
    error_message = "SNS must use encryption by default."
  }
  assert {
    condition     = aws_cloudwatch_log_group.processor.retention_in_days == 30
    error_message = "Log retention default changed."
  }
  assert {
    condition     = jsondecode(aws_sqs_queue_policy.eventbridge_dlq.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"] != null
    error_message = "DLQ policy must restrict source rule ARNs."
  }
  assert {
    condition     = alltrue([for statement in jsondecode(aws_iam_role_policy.processor.policy).Statement : !contains(flatten([statement.Action]), "iam:*")])
    error_message = "Lambda role contains a wildcard IAM action."
  }
  assert {
    condition     = local.common_tags["Project"] == "aws-security-hub-workflow" && local.common_tags["ManagedBy"] == "Terraform"
    error_message = "Required default tags are missing."
  }
}

run "asff_compatibility" {
  command = apply
  variables { finding_schema_mode = "asff" }
  assert {
    condition     = length(aws_cloudwatch_event_rule.findings) == 1 && jsondecode(aws_cloudwatch_event_rule.findings["asff"].event_pattern)["detail-type"][0] == "Security Hub Findings - Imported"
    error_message = "ASFF compatibility routing is incorrect."
  }
}

run "dual_teaching_mode" {
  command = apply
  variables { finding_schema_mode = "dual" }
  assert {
    condition     = length(aws_cloudwatch_event_rule.findings) == 2
    error_message = "Dual mode must create separate OCSF and ASFF rules."
  }
}

run "invalid_schema_mode" {
  command = plan
  variables { finding_schema_mode = "invalid" }
  expect_failures = [var.finding_schema_mode]
}
