# v0.1.0 release notes

SPDX-License-Identifier: MIT-0

Initial educational reference release for an event-driven AWS Security Hub finding
workflow built with Terraform and Python.

## Included

- Separate OCSF `Findings Imported V2` and Security Hub CSPM ASFF
  `Security Hub Findings - Imported` adapters.
- Schema-aware validation into a bounded normalized finding model.
- Explainable JSON triage decisions: `ESCALATE`, `RECORD`, `IGNORE`, `REJECT`, and
  `DUPLICATE`, each with a stable reason code.
- DynamoDB-backed AWS Lambda Powertools idempotency with TTL and concurrent-delivery
  protection.
- Minimal sanitized SNS escalation messages.
- EventBridge retry policy and SQS target-delivery DLQ.
- Structured Powertools logs, EMF metrics, retention, and CloudWatch alarms.
- Terraform mocked tests, Python behavior/security tests, deterministic local fixtures,
  reproducible Lambda packaging, and SHA-pinned CI workflows.
- Deployment, cleanup, cost, security, compatibility, threat-model, presentation, and
  article documentation.

## Safety boundaries

This release does not enable Security Hub, Security Hub CSPM, GuardDuty, Inspector,
Macie, AWS Config, or Organizations. It does not retrieve or modify affected resources,
generate attack traffic, automatically subscribe SNS endpoints, or perform remediation.
Synthetic fixtures are unmistakably labeled and contain no real account or finding data.

## Compatibility

- Terraform `>= 1.10.0, < 2.0.0`; validated with 1.15.8.
- AWS Provider `>= 6.54.0, < 7.0.0`; lockfile selects 6.62.0.
- AWS Lambda Python 3.13 on arm64.
- OCSF is the default. ASFF is an optional Security Hub CSPM compatibility path.
- `dual` is for migration or teaching and can surface logical duplicates across schemas.

## Known limitations

- The reference has not been deployed by the release automation and makes no
  production-readiness or compliance claim.
- Idempotency suppresses repeated deliveries of the same schema/update key; it does not
  semantically correlate OCSF and ASFF findings.
- EventBridge's DLQ covers failed target delivery, not an application exception after a
  successful Lambda invocation.
- Severity-only triage is intentionally simple and does not represent organizational
  risk.
- Regional service and integration availability must be checked before deployment.
- No multi-account routing, cross-Region configuration, dashboard, S3 decision records,
  ticketing, or automated remediation is included.

See `README.md`, `docs/deployment.md`, and `docs/costs-and-cleanup.md` before any manual
AWS deployment.
