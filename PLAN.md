# Implementation plan

SPDX-License-Identifier: MIT-0

## Confirmed architecture

Security Hub OCSF `Findings Imported V2` and optional Security Hub CSPM ASFF
`Security Hub Findings - Imported` events use separate EventBridge rules and schema
adapters. Both converge on one normalized finding, an explainable JSON triage policy,
DynamoDB-backed Powertools idempotency, and a minimal SNS notification. EventBridge
target delivery failures go to a same-Region SQS standard DLQ. Logs and EMF metrics
go to CloudWatch. There is no remediation path.

## Scope and assumptions

- Version 1 deploys only EventBridge, Lambda, DynamoDB, SNS, SQS, IAM, CloudWatch
  logs, and alarms. It does not enable any account-level security service.
- `ocsf` is the default; `asff` and `dual` are compatibility modes. Dual can receive
  logical duplicates and is intended for teaching or migration.
- The deployment Region already supports the desired Security Hub capability.
- Security Hub/Security Hub CSPM and upstream integrations are prerequisites managed
  outside this Terraform state.
- Service-managed encryption is the default. An existing SNS KMS key can be supplied.
- Local state is acceptable only for a personal demo; teams supply an existing S3
  backend with versioning, encryption, least privilege, and S3 lockfiles.

## Documentation questions resolved

- Current Security Hub uses OCSF `Findings Imported V2`; Security Hub CSPM uses ASFF
  `Security Hub Findings - Imported`. Each event contains one finding.
- Python 3.13 is the selected Lambda runtime.
- Terraform and provider constraints are bounded and all version 1 resources are
  supported by the AWS Provider.
- Security Hub enablement is deliberately outside this workflow state as a lifecycle
  and cost boundary.

Current versions, regional caveats, and primary references are maintained in
`docs/research-notes.md` rather than duplicated here.

## Security boundaries

Untrusted findings cross Security Hub → EventBridge → Lambda. The Lambda role is a
separate boundary for DynamoDB, SNS, logs, and EMF. Terraform state and the future
GitHub-to-AWS OIDC relationship are deployment boundaries. Validation, minimization,
redaction, least privilege, source-ARN restrictions, idempotency, and explicit failure
handling apply at these boundaries.

## Testing strategy

Unit and security tests cover envelopes, both adapters, sanitization, triage,
notification construction, Powertools DynamoDB idempotency including concurrency and
failure behavior, configuration, observability degradation, and handler outcomes. AWS
calls use injected fakes or botocore Stubber. Native Terraform tests use a mocked provider
and assert resource semantics. CI runs formatting, linting, typing, coverage,
packaging, Terraform validation/tests, TFLint, Trivy configuration scanning,
markdownlint, pip-audit, CodeQL, and Scorecard without AWS credentials.
