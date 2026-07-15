# SPDX-License-Identifier: MIT-0
provider "aws" {
  region              = var.aws_region
  allowed_account_ids = length(var.allowed_aws_account_ids) > 0 ? var.allowed_aws_account_ids : null

  default_tags {
    tags = local.common_tags
  }
}

