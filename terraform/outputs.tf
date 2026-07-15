# SPDX-License-Identifier: MIT-0
output "lambda_function_name" {
  description = "Finding processor Lambda function name."
  value       = aws_lambda_function.processor.function_name
}

output "sns_topic_arn" {
  description = "Escalation SNS topic ARN; subscriptions are intentionally not created."
  value       = aws_sns_topic.escalation.arn
}

output "idempotency_table_name" {
  description = "Ephemeral Powertools idempotency table name."
  value       = aws_dynamodb_table.idempotency.name
}

output "eventbridge_rule_arns" {
  description = "EventBridge finding rule ARNs by schema family."
  value       = { for family, rule in aws_cloudwatch_event_rule.findings : family => rule.arn }
}

output "eventbridge_dlq_url" {
  description = "SQS URL for failed EventBridge target deliveries."
  value       = aws_sqs_queue.eventbridge_dlq.url
}

