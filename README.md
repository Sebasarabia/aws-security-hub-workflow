# AWS Security Hub workflow

An educational Terraform and Python reference that routes AWS security findings through
EventBridge to one Lambda processor for schema validation, normalization, explainable
triage, duplicate suppression, and minimal SNS escalation. It accompanies a Road to AWS
Community Day Bolivia presentation and is suitable as a reproducible article companion.

> **Educational sample:** This community project is not owned, supported, certified, or
> endorsed by AWS. It is not production-ready, does not establish compliance, and must be
> adapted to your risk, operations, retention, and incident-response requirements.

## Security Hub terminology

Current **AWS Security Hub** uses OCSF 1.6 findings and emits one finding per EventBridge
`Findings Imported V2` event. **AWS Security Hub CSPM** is the posture-management and ASFF
compatibility path; it emits one finding per `Security Hub Findings - Imported` event.
They are separate adapters. OCSF is the default. `dual` exists for migration and teaching
and can produce logical duplicates depending on account configuration.

## Architecture

```text
Security Hub (OCSF) ─┐
                     ├─> EventBridge ─> Lambda ─┬─> DynamoDB idempotency
Security Hub CSPM ───┘            │             ├─> SNS escalation
      (ASFF, optional)             └─failure─> SQS DLQ
                                                └─> CloudWatch logs/metrics
```

EventBridge performs coarse source/type routing. Lambda distrusts and validates the
envelope and its single finding, calls the correct adapter, sanitizes fields, evaluates
the versioned policy, applies Powertools idempotency, emits a small decision record and
metrics, and publishes only escalations. No raw event is logged or stored.

## Deliberate exclusions

This version does not enable Security Hub, Security Hub CSPM, GuardDuty, Inspector, Macie,
AWS Config, or Organizations; retrieve or modify affected resources; create email
subscriptions; store raw findings; generate attack traffic; or perform remediation.

## Prerequisites

- Python 3.13, `make`, and `zip` for local work
- Terraform 1.10–1.x, TFLint, Trivy, and Node.js/`npx` for the full check
- Only for deployment: an AWS account/Region where the chosen capability is already
  enabled, a preconfigured identity, and an explicit account allowlist

## Local quick start (no AWS account)

```bash
git clone https://github.com/Sebasarabia/aws-security-hub-workflow.git
cd aws-security-hub-workflow
make setup
make check
make demo-local-ocsf
make demo-local-asff
```

The fixtures use account `000000000000`, invented identifiers, and explicit synthetic
labels. The local demos use test doubles and do not resolve AWS credentials.

## Terraform validation

```bash
make package
make terraform-fmt
make terraform-validate
make terraform-test
```

`terraform test` uses a mocked AWS Provider and needs no credentials. `make package`
bundles exact runtime dependencies for Python 3.13/arm64 and writes a SHA-256 checksum.

## Deployment

Deployment is deliberately separate from the quick start. Read
[`docs/deployment.md`](docs/deployment.md), [`docs/security-design.md`](docs/security-design.md),
and [`docs/costs-and-cleanup.md`](docs/costs-and-cleanup.md) first. Then build the package,
copy `terraform/terraform.tfvars.example` to an ignored `.tfvars`, replace the example
account ID, inspect `terraform plan`, and apply manually only after approval. There is no
deployment workflow or `make deploy` command.

## Demo paths

The deterministic local OCSF and ASFF paths test the processor. A deployed real-finding
path additionally tests the existing Security Hub capability and EventBridge. Synthetic
events are not incidents. See [`docs/demo-runbook.md`](docs/demo-runbook.md).

## Configuration

| Input | Default | Purpose |
|---|---:|---|
| `finding_schema_mode` | `ocsf` | `ocsf`, `asff`, or `dual` routing |
| `allowed_aws_account_ids` | empty | Provider wrong-account safeguard; set before deploy |
| `aws_region` | `us-east-1` | Single deployment Region |
| `idempotency_expiry_seconds` | `86400` | Duplicate suppression window |
| `log_retention_days` | `30` | Explicit processing-log retention |
| `log_level` | `INFO` | Powertools JSON log level |
| `sns_kms_key_arn` | `null` | Existing key, otherwise `alias/aws/sns` |

Policy lives in [`config/triage-policy.json`](config/triage-policy.json). Severity is only
an explainable demonstration input, not a claim about organizational risk. Future context
could include criticality, exposure, account purpose, data sensitivity, exploitability,
repetition, environment, ownership, and business impact.

## Security, costs, cleanup, and limitations

Review the [threat model](docs/threat-model.md) and [security design](docs/security-design.md).
The main costs are usage-based Lambda, EventBridge, DynamoDB, SNS, SQS, and CloudWatch;
pre-existing security services can cost substantially more and are outside this state.
See [costs and cleanup](docs/costs-and-cleanup.md). Regional support and integration
availability differ. EventBridge's target DLQ covers delivery failure, not a Lambda
application error after successful invocation. For bursts, backpressure, independent
consumers, multiple consumers, or explicit replay, insert SQS before Lambda.

Repository-owner settings such as branch rules, private vulnerability reporting, and
push protection are documented in
[GitHub repository settings](docs/github-repository-settings.md).

## Contributing and security reporting

See [CONTRIBUTING.md](CONTRIBUTING.md) for checks and [SECURITY.md](SECURITY.md) for private
reporting guidance. Participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
Release gates and the prepared `v0.1.0` notes are documented in
[the release process](docs/release-process.md).

## License

Licensed under the [MIT No Attribution License (MIT-0)](LICENSE).
