# SPDX-License-Identifier: MIT-0
variable "aws_region" {
  description = "AWS Region for all workflow resources; verify Security Hub capability availability first."
  type        = string
  default     = "us-east-1"
  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS Region identifier."
  }
}

variable "allowed_aws_account_ids" {
  description = "Optional account allowlist safety guard. Set this before deployment."
  type        = set(string)
  default     = []
  validation {
    condition     = alltrue([for id in var.allowed_aws_account_ids : can(regex("^[0-9]{12}$", id))])
    error_message = "Every allowed account ID must contain exactly 12 digits."
  }
}

variable "project_name" {
  description = "Short name used for resource names and tags."
  type        = string
  default     = "security-hub-workflow"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.project_name))
    error_message = "project_name must be 3-32 lowercase letters, digits, or hyphens."
  }
}

variable "environment" {
  description = "Environment tag and name suffix."
  type        = string
  default     = "demo"
  validation {
    condition     = contains(["demo", "development", "test", "production"], var.environment)
    error_message = "environment must be demo, development, test, or production."
  }
}

variable "finding_schema_mode" {
  description = "Finding family to route: ocsf (current Security Hub), asff (Security Hub CSPM), or dual migration mode."
  type        = string
  default     = "ocsf"
  validation {
    condition     = contains(["ocsf", "asff", "dual"], var.finding_schema_mode)
    error_message = "finding_schema_mode must be ocsf, asff, or dual."
  }
}

variable "lambda_package_path" {
  description = "Path, relative to terraform/, to the pre-built Lambda zip. Run make package first."
  type        = string
  default     = "../build/finding-processor.zip"
}

variable "lambda_timeout_seconds" {
  description = "Processor timeout in seconds."
  type        = number
  default     = 30
  validation {
    condition     = var.lambda_timeout_seconds >= 10 && var.lambda_timeout_seconds <= 60
    error_message = "lambda_timeout_seconds must be between 10 and 60."
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period."
  type        = number
  default     = 30
  validation {
    condition     = contains([7, 14, 30, 60, 90, 120, 150, 180, 365], var.log_retention_days)
    error_message = "log_retention_days must be a supported CloudWatch retention value."
  }
}

variable "log_level" {
  description = "Powertools structured logging level. DEBUG can increase cost and should be temporary."
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
  }
}

variable "idempotency_expiry_seconds" {
  description = "Seconds before Powertools idempotency records can be reused."
  type        = number
  default     = 86400
  validation {
    condition     = var.idempotency_expiry_seconds >= 60 && var.idempotency_expiry_seconds <= 2592000
    error_message = "idempotency expiry must be between 60 seconds and 30 days."
  }
}

variable "event_maximum_age_seconds" {
  description = "Maximum EventBridge delivery age."
  type        = number
  default     = 3600
  validation {
    condition     = var.event_maximum_age_seconds >= 60 && var.event_maximum_age_seconds <= 86400
    error_message = "event maximum age must be 60-86400 seconds."
  }
}

variable "event_retry_attempts" {
  description = "EventBridge target retry attempts."
  type        = number
  default     = 10
  validation {
    condition     = var.event_retry_attempts >= 0 && var.event_retry_attempts <= 185
    error_message = "event_retry_attempts must be 0-185."
  }
}

variable "sns_kms_key_arn" {
  description = "Optional existing customer-managed KMS key ARN for SNS; null uses alias/aws/sns."
  type        = string
  default     = null
  nullable    = true
  validation {
    condition     = var.sns_kms_key_arn == null || can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/", var.sns_kms_key_arn))
    error_message = "sns_kms_key_arn must be a KMS key ARN or null."
  }
}

variable "additional_tags" {
  description = "Additional non-sensitive resource tags."
  type        = map(string)
  default     = {}
}
