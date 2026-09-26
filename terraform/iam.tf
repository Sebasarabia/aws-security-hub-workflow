# SPDX-License-Identifier: MIT-0
resource "aws_iam_role" "processor" {
  name = "${local.name}-processor"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "processor" {
  name = "${local.name}-processor"
  role = aws_iam_role.processor.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Sid      = "WriteOwnLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.processor.arn}:*"
      },
      {
        Sid      = "UseIdempotencyTable"
        Effect   = "Allow"
        Action   = ["dynamodb:DeleteItem", "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.idempotency.arn
      },
      {
        Sid      = "PublishMinimalEscalation"
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.escalation.arn
      }
      ], var.sns_kms_key_arn == null ? [] : [
      {
        Sid      = "UseExistingSnsKey"
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey", "kms:GenerateDataKeyWithoutPlaintext"]
        Resource = var.sns_kms_key_arn
      }
    ])
  })
}
