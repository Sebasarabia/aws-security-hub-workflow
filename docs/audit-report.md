# Implementation audit summary

SPDX-License-Identifier: MIT-0

Initial audit: **2026-08-29**. Public-record review: **2026-09-26**.

This document summarizes the current repository state. Detailed version research belongs
in `docs/research-notes.md`; sanitized AWS evidence belongs in
`docs/deployment-validation.md`. This separation reduces duplication and prevents dated
operational details from being mistaken for permanent project guarantees.

## Outcome

The required version 1 reference workflow is implemented and passes its local Python,
Terraform, packaging, documentation, and security gates. It remains an educational
reference, not a production-readiness or compliance claim.

The public `v0.1.0` tag is immutable. Later changes on `main`, including dependency,
CodeQL, validation, IAM, tag-protection, and documentation updates, require a future
release before they should be described as part of a published version.

## Current terminology and event paths

- **AWS Security Hub** is the preferred OCSF path. EventBridge receives
  `Findings Imported V2` events containing one finding.
- **AWS Security Hub CSPM** is the optional ASFF compatibility path. EventBridge receives
  `Security Hub Findings - Imported` events containing one finding.
- `ocsf` is the default mode. `asff` is a compatibility mode. `dual` is a migration or
  teaching mode that may produce logically duplicated signals.
- OCSF and ASFF field access is isolated in separate adapters before normalization.

## Implemented workflow

The Terraform root configuration creates only the workflow resources:

- EventBridge rule and direct Lambda target for each selected schema family;
- Lambda invocation permission restricted to the corresponding rule ARN;
- SQS target-delivery DLQ and source-restricted queue policy;
- Python 3.13 arm64 Lambda and explicit CloudWatch log retention;
- on-demand, encrypted DynamoDB idempotency table with TTL;
- encrypted SNS escalation topic without automatic subscriptions;
- least-privilege Lambda execution role; and
- alarms for Lambda errors, throttles, DLQ messages, and notification failures.

Terraform does not enable Security Hub, Security Hub CSPM, GuardDuty, Inspector, Macie,
AWS Config, or Organizations. It does not create a Terraform backend, email subscription,
attack workload, affected-resource integration, or remediation path.

The Python processor provides:

- bounded EventBridge and finding validation;
- independent OCSF and ASFF adapters;
- one normalized internal finding model;
- Unicode-preserving sanitization and identifier masking;
- explainable policy decisions with machine-readable reasons;
- DynamoDB-backed Powertools idempotency;
- minimized deterministic SNS notifications; and
- structured logs and low-cardinality metrics without raw-event logging.

## Security controls

- Provider account allowlist and no hard-coded real account IDs.
- Source-ARN restrictions for EventBridge-to-Lambda and EventBridge-to-DLQ access.
- Resource-scoped DynamoDB, SNS, log, and optional SNS KMS permissions.
- Service-managed encryption by default; an existing compatible SNS KMS key is optional.
- Required project and management tags cannot be replaced by additional user tags.
- No raw finding persistence or complete finding content in logs or notifications.
- Concurrency-safe duplicate suppression with configurable expiration.
- Explicit separation of delivery failure, processing error, malformed input, duplicate,
  and intentional ignore outcomes.
- Exact runtime dependency pins, provider lockfile, deterministic packaging, CodeQL,
  dependency auditing, IaC scanning, and SHA-pinned GitHub Actions.
- Read-only workflow permissions by default and no active AWS deployment workflow.

The threat analysis and design rationale are maintained in `docs/threat-model.md` and
`docs/security-design.md`.

## Validation results

The 2026-09-26 repository validation produced:

- Ruff formatting and linting: pass;
- Mypy strict checking: pass;
- Pytest: **60 passed**;
- overall branch-aware coverage: **95.30%**;
- Terraform formatting and validation: pass;
- native mocked Terraform tests: **7 passed**, without AWS credentials;
- TFLint: pass;
- Trivy configuration scan: **0 HIGH/CRITICAL findings**;
- `pip-audit`: no known vulnerabilities in runtime requirements;
- actionlint and Markdownlint: pass;
- OCSF and ASFF local demonstrations: pass without AWS credentials; and
- two package builds: identical SHA-256 output.

The repository scan found no tracked Terraform state, plans, private variable files,
build ZIPs, IDE metadata, or credential-shaped secrets.

One narrow Trivy suppression remains in `terraform/notifications.tf` for the deliberate
AWS-managed SNS encryption default. The project documents the cost and key-policy
tradeoffs and permits an existing customer-managed key; the scanner is not disabled
globally.

## AWS validation boundary

An earlier explicitly authorized sandbox deployment validated the intended Terraform
resources, read-only control checks, synthetic first/duplicate/rejected processing, and
idempotent notification behavior. A later owner-operated check confirmed that AWS-owned
Security Hub `Findings Imported V2` events traversed EventBridge and the Lambda processor
in one account and Region.

The public record intentionally omits account identifiers, local profile names, raw
findings, request IDs, resource ARNs, notification payloads, and account-specific finding
counts. See `docs/deployment-validation.md` for the bounded evidence and limitations.

The 2026-09-26 source refresh itself made no AWS API calls and was not deployed.

## CI and repository controls

- `ci.yml` runs Python, packaging, dependency, Terraform, TFLint, Trivy, actionlint, and
  Markdown checks without AWS credentials.
- `codeql.yml` analyzes Python and GitHub Actions.
- `scorecard.yml` uses the official OpenSSF workflow with explicit permissions.
- Dependabot monitors pip, Terraform, and GitHub Actions.
- Third-party actions use complete immutable commit SHAs.
- No workflow uses `pull_request_target`, long-lived AWS keys, or automatic deployment.

GitHub-hosted settings can change independently of the repository. The recommended
branch-protection and security checklist is in `docs/github-repository-settings.md` and
must be rechecked for each release.

## Known limitations

- Validation in one sandbox account and Region does not establish production,
  multi-account, or cross-Region behavior.
- Event schemas and regional integrations can change and require adapter maintenance.
- Dual mode does not correlate semantically equivalent OCSF and ASFF findings.
- The EventBridge target DLQ does not capture application failure after a successful
  Lambda invocation.
- Severity-based triage lacks organizational context and is not a risk score.
- Notification ownership, thresholds, and cost controls remain deployment-specific.
- The project is not certified, compliant, or represented as a complete SOAR platform.

## Optional features not implemented

Version 1 does not implement S3 decision records, generated KMS keys, finding updates,
sample-finding generation, CSPM custom import, dashboards, multi-account routing,
cross-Region examples, ticketing, Step Functions, Systems Manager Automation, GitHub OIDC
deployment, or automated remediation.

## Safety record

- No AWS credential, static secret, full account identifier, or real finding is committed.
- No attack traffic or intentionally vulnerable resource was generated.
- No automatic remediation or affected-resource modification exists.
- The repository does not disable pre-existing account-level security services.
- The 2026-09-26 refresh changed source and documentation only; it did not create, modify,
  or delete AWS resources.
