# Deployment validation record

SPDX-License-Identifier: MIT-0

Verification date: **2026-08-29**. Region: **us-east-1**. This record intentionally
masks account and principal identifiers and contains no credentials, Terraform state,
request IDs, or raw findings.

## Validated before apply

- Terraform 1.16.0 was downloaded from HashiCorp and its published SHA-256 verified.
- AWS Provider 6.62.0 matched the committed dependency lockfile.
- The Lambda artifact was rebuilt from exact runtime pins with SHA-256
  `b71d666d0601da101e4a80acdad2fe06a09bb7055088150f92b003418f726202`.
- `terraform validate` passed.
- The saved OCSF plan targeted the explicitly allowlisted account and contained
  **15 creates, 0 changes, and 0 destroys**.
- The plan did not enable Security Hub, Security Hub CSPM, GuardDuty, Inspector, Macie,
  AWS Config, Organizations, subscriptions, attacks, or remediation.

## Initial default-profile attempt

An explicitly authorized apply of the reviewed plan was attempted against the default
CLI profile. The AWS identity was valid, but its identity policies denied required
actions including creation of IAM, DynamoDB, SQS, SNS, CloudWatch Logs, and alarms.
EventBridge rule creation reached tag authorization and was denied at
`events:TagResource`.

Terraform recorded no managed resources in local state after the failed apply. A
read-only check confirmed that the intended SQS queue did not exist. The same identity
lacked read permissions for EventBridge, Lambda, DynamoDB, SNS, IAM, Logs, CloudWatch,
and Security Hub, so this audit cannot conclusively assert that no partial EventBridge
rule exists. A retry with sufficient permissions is idempotent for the fixed rule name,
but the account must be inspected by an authorized operator if deployment is abandoned.

## Authorized SS5 deployment

The repository owner explicitly selected the configured SS5 profile. Security Hub is not
subscribed in that account in `us-east-1`; Terraform did not enable it. A new plan with
an explicit account allowlist contained **15 creates, 0 changes, and 0 destroys**. The saved
plan created the intended OCSF-mode workflow resources. A post-apply refresh returned
`No changes`, and local state records all 15 resources.

The enhanced read-only verifier confirmed:

- Lambda active on Python 3.13/arm64 with the reviewed environment, timeout, and package
  checksum;
- DynamoDB active with on-demand billing, service-managed encryption, TTL enabled, and
  PITR disabled;
- SNS encrypted with `alias/aws/sns` and no subscriptions;
- EventBridge enabled with one Lambda target, bounded retry policy, and the intended
  SQS DLQ;
- DLQ empty, service-encrypted, and restricted to the intended EventBridge rule;
- Lambda resource policy restricted to the intended rule;
- Lambda execution policy has no wildcard actions or wildcard resources;
- explicit 30-day log retention and all four required alarms.

## Synthetic runtime validation

The deployed Lambda was invoked only with repository-owned synthetic fixtures:

1. First OCSF delivery returned `ESCALATE / POLICY_SEVERITY_ESCALATION`.
2. The exact duplicate returned `DUPLICATE / IDEMPOTENCY_RECORD_EXISTS`.
3. An empty finding collection returned
   `REJECT / EVENT_MUST_CONTAIN_EXACTLY_ONE_FINDING` without a Lambda function error.

CloudWatch recorded exactly one native SNS publication for the two identical valid
invocations, demonstrating that the duplicate did not repeat the side effect. The SNS
topic had no subscriptions, so no message was delivered to a person or external system.

CloudWatch Logs contained JSON decision/rejection records and EMF metrics for received,
validated, escalated, duplicate, rejected, and processing latency outcomes. The fixture's
raw title, description, and resource identifier were absent from the inspected logs. The
deployed EventBridge pattern matched the synthetic OCSF fixture through the read-only
`TestEventPattern` API, but no custom event impersonated the AWS-owned source.

## Remaining limitation and cleanup responsibility

This validates the deployed infrastructure and Lambda behavior, not real Security Hub
delivery. SS5 has no Security Hub subscription, so an AWS-owned `Findings Imported V2`
event did not traverse EventBridge. Do not describe the synthetic invocation or pattern
test as a real incident or end-to-end Security Hub integration.

The ignored local Terraform state is the authoritative state for this demo deployment
and must be preserved until cleanup. Follow `docs/costs-and-cleanup.md` and review a
destroy plan before removing the 15 resources. Terraform must not enable or disable
account-level security services during cleanup.
