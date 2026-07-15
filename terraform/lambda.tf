# SPDX-License-Identifier: MIT-0
resource "aws_cloudwatch_log_group" "processor" {
  name              = "/aws/lambda/${local.name}-processor"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "processor" {
  function_name    = "${local.name}-processor"
  description      = "Validates, normalizes, and triages Security Hub findings without remediation"
  role             = aws_iam_role.processor.arn
  runtime          = "python3.13"
  architectures    = ["arm64"]
  handler          = "finding_processor.handler.lambda_handler"
  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)
  timeout          = var.lambda_timeout_seconds
  memory_size      = 256

  environment {
    variables = {
      FINDING_SCHEMA_MODE          = var.finding_schema_mode
      IDEMPOTENCY_TABLE            = aws_dynamodb_table.idempotency.name
      IDEMPOTENCY_EXPIRY_SECONDS   = tostring(var.idempotency_expiry_seconds)
      NOTIFICATION_TOPIC_ARN       = aws_sns_topic.escalation.arn
      TRIAGE_POLICY_PATH           = "config/triage-policy.json"
      POWERTOOLS_SERVICE_NAME      = "finding-processor"
      POWERTOOLS_METRICS_NAMESPACE = "SecurityHubWorkflow"
      LOG_LEVEL                    = "INFO"
    }
  }

  tracing_config {
    mode = "PassThrough"
  }

  depends_on = [aws_cloudwatch_log_group.processor]
}

