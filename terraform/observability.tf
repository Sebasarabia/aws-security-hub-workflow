# SPDX-License-Identifier: MIT-0
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name}-lambda-errors"
  alarm_description   = "Processor returned an application error"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.name}-lambda-throttles"
  alarm_description   = "Processor was throttled"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "dlq_visible" {
  alarm_name          = "${local.name}-dlq-visible"
  alarm_description   = "EventBridge could not deliver one or more events"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    QueueName = aws_sqs_queue.eventbridge_dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "notification_failures" {
  alarm_name          = "${local.name}-notification-failures"
  alarm_description   = "SNS publication failed in the processor"
  namespace           = "SecurityHubWorkflow"
  metric_name         = "NotificationFailures"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    service = "finding-processor"
  }
}
