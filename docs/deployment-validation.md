# Deployment validation record

SPDX-License-Identifier: MIT-0

Initial verification: **2026-08-29**. Public-record review: **2026-09-26**. Region:
**us-east-1**. This record intentionally masks account and principal identifiers and
contains no credentials, Terraform state, request IDs, or raw findings.

## Validated before apply

- Terraform 1.16.0 was downloaded from HashiCorp and its published SHA-256 verified.
- AWS Provider 6.62.0 matched the then-committed dependency lockfile.
- The Lambda artifact was rebuilt from exact runtime pins with SHA-256
  `b71d666d0601da101e4a80acdad2fe06a09bb7055088150f92b003418f726202`.
- `terraform validate` passed.
- The saved OCSF plan targeted the explicitly allowlisted account and contained only the
  intended workflow creates, with no changes or destroys.
- The plan did not enable Security Hub, Security Hub CSPM, GuardDuty, Inspector, Macie,
  AWS Config, Organizations, subscriptions, attacks, or remediation.

## Authorized sandbox deployment

The repository owner explicitly selected an authorized sandbox account. A plan with an
explicit account allowlist contained only the intended Terraform-managed resource
creates, with no changes or destroys. The saved plan created the intended OCSF-mode
workflow resources. A post-apply refresh returned `No changes`.

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

## Subsequent end-to-end validation

After Security Hub Essentials was enabled outside this Terraform stack in `us-east-1`,
the deployed rule received AWS-owned `Findings Imported V2` events and invoked the
processor. CloudWatch showed received and validated findings, policy decisions across
`ESCALATE`, `RECORD`, and `IGNORE`, and no observed Lambda errors, throttles,
notification failures, or visible DLQ messages during the validation window.

This confirms the deployed Security Hub to EventBridge to Lambda path in one account and
Region. Exact counts are intentionally omitted because they are an account-specific
operational snapshot, not a reproducible benchmark; findings are not unique resources or
confirmed incidents. SNS had no subscriptions, so accepted publications were not
delivered to a person or external endpoint. No raw finding, account identifier, resource
ARN, or notification content is included in this public record.

## Remaining limitations and cleanup responsibility

The validation does not establish production readiness, multi-account behavior,
cross-Region behavior, response ownership, or incident confirmation. It also does not
turn a finding into proof of an attack. Terraform continues to exclude account-level
service enablement.

The ignored local Terraform state is the authoritative state for this demo deployment
and must be preserved until cleanup. Follow `docs/costs-and-cleanup.md` and review a
destroy plan before removing the managed resources. Terraform must not enable or disable
account-level security services during cleanup.

The 2026-09-26 local refresh now validates Terraform 1.16.4, AWS Provider 6.66.0, and a
new dependency-built Lambda artifact. Those working-tree changes were not deployed and
do not retroactively alter the dated sandbox evidence above.
