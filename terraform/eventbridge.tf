# SPDX-License-Identifier: MIT-0
resource "aws_sqs_queue" "eventbridge_dlq" {
  name                      = "${local.name}-eventbridge-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_cloudwatch_event_rule" "findings" {
  for_each      = local.event_patterns
  name          = "${local.name}-${each.key}-findings"
  description   = "Routes ${upper(each.key)} findings to the validation processor"
  event_pattern = jsonencode(each.value)
}

resource "aws_cloudwatch_event_target" "processor" {
  for_each = aws_cloudwatch_event_rule.findings
  rule     = each.value.name
  arn      = aws_lambda_function.processor.arn

  dead_letter_config {
    arn = aws_sqs_queue.eventbridge_dlq.arn
  }

  retry_policy {
    maximum_event_age_in_seconds = var.event_maximum_age_seconds
    maximum_retry_attempts       = var.event_retry_attempts
  }
}

resource "aws_lambda_permission" "eventbridge" {
  for_each      = aws_cloudwatch_event_rule.findings
  statement_id  = "AllowEventBridge${title(each.key)}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = each.value.arn
}

resource "aws_sqs_queue_policy" "eventbridge_dlq" {
  queue_url = aws_sqs_queue.eventbridge_dlq.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowIntendedRulesOnly"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.eventbridge_dlq.arn
      Condition = { ArnEquals = { "aws:SourceArn" = [for rule in aws_cloudwatch_event_rule.findings : rule.arn] } }
    }]
  })
}
