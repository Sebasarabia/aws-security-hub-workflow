# SPDX-License-Identifier: MIT-0
locals {
  name = "${var.project_name}-${var.environment}"
  common_tags = merge({
    Project     = "aws-security-hub-workflow"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "EducationalReference"
  }, var.additional_tags)

  event_patterns = {
    for family, pattern in {
      ocsf = {
        source        = ["aws.securityhub"]
        "detail-type" = ["Findings Imported V2"]
      }
      asff = {
        source        = ["aws.securityhub"]
        "detail-type" = ["Security Hub Findings - Imported"]
      }
    } : family => pattern if var.finding_schema_mode == family || var.finding_schema_mode == "dual"
  }
}

