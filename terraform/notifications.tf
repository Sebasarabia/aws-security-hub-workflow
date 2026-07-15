# SPDX-License-Identifier: MIT-0
resource "aws_sns_topic" "escalation" {
  name = "${local.name}-escalation"
  #trivy:ignore:AWS-0136 -- Service-managed encryption is deliberate; a sample-only CMK adds cost and key-policy risk.
  kms_master_key_id = coalesce(var.sns_kms_key_arn, "alias/aws/sns")
}
