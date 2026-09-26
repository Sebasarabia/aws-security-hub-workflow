# Implementation audit report

SPDX-License-Identifier: MIT-0

Audit date: **2026-08-29**. Public-record update: **2026-09-26**.
Repository: `Sebasarabia/aws-security-hub-workflow`
Published release version: **0.1.0** / tag **v0.1.0**
Audit scope: source, tests, Terraform, packaging, CI configuration, documentation,
authenticated GitHub controls, the explicitly authorized AWS deployment, and subsequent
end-to-end finding delivery validation.

## Executive outcome

The required version 1 reference implementation is present and passes its local quality,
security, packaging, and mocked Terraform gates. The audit corrected dependency drift,
expanded idempotency and failure tests, strengthened Terraform/IAM assertions, fixed two
observability configuration defects, and prepared release documentation.

The 2026-09-26 working-tree refresh also removed stale/account-specific operational
details, completed the optional existing-KMS-key IAM path, protected required tags from
user overrides, made the deployed verifier configuration-aware, refreshed supported
tool/dependency pins, and moved CodeQL to v4. These changes are not part of the immutable
`v0.1.0` tag until a later reviewed release is published.

The repository is published as **v0.1.0**. PRs #15 and #17 were merged to protected
`main`; repository metadata, required checks, secret scanning, push protection,
Dependabot security features, and private vulnerability reporting were applied and
verified through the authenticated GitHub API.

The repository owner selected an authorized sandbox account. A plan containing only the
intended creates, with no changes or destroys, was applied successfully; a post-apply
plan returned `No changes`. Infrastructure controls and direct synthetic Lambda behavior
passed. After Security Hub Essentials was enabled outside this Terraform stack, AWS-owned
`Findings Imported V2` events traversed the deployed EventBridge-to-Lambda path
successfully.

## Technical reconciliation

- The initial release audit used Terraform **1.16.0** and AWS Provider **6.62.0**. The
  2026-09-26 refresh verified Terraform **1.16.4**, updated the signed provider lock to
  **6.66.0**, and reran native Terraform validation/tests. Configuration remains
  `>= 1.10.0, < 2.0.0` with AWS Provider `>= 6.54.0, < 7.0.0`.
- Lambda Python 3.13 and 3.14 are stable supported AL2023 runtimes. Python 3.15 is public
  preview, so the project deliberately remains on **Python 3.13/arm64**.
- Powertools for AWS Lambda (Python) **3.35.0** is selected and used for JSON logging,
  EMF metrics, and DynamoDB idempotency.
- Runtime dependencies are exact-pinned, including Boto3 **1.43.103**. The Lambda package
  does not rely on the runtime-provided SDK.
- The refreshed Pydantic 2.13.5 dependency set was resolved before pinning and uses its
  compatible Pydantic Core 2.46.5 release.
- Current Security Hub terminology and EventBridge contracts were rechecked against AWS
  documentation. Full links and regional caveats are in `docs/research-notes.md`.

## Security Hub terminology used

- **AWS Security Hub**: preferred OCSF 1.6 path, EventBridge source
  `aws.securityhub`, detail type `Findings Imported V2`, one finding per event.
- **AWS Security Hub CSPM**: optional ASFF compatibility path, source
  `aws.securityhub`, detail type `Security Hub Findings - Imported`, one finding per
  event.
- `ocsf` is the default. `asff` is compatibility mode. `dual` is explicitly a migration
  or teaching mode and can produce logically duplicated signals.
- OCSF and ASFF field access remains isolated in separate adapters before normalization.

## Repository layout

```text
.
├── .github/
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   ├── release.yml
│   └── workflows/{ci,codeql,scorecard}.yml
├── config/triage-policy.json
├── docs/
│   ├── adr/0001..0004
│   ├── architecture, compatibility, deployment, security, threat-model docs
│   ├── research-notes.md
│   ├── deployment-validation.md
│   ├── github-repository-settings.md
│   ├── release-process.md
│   ├── release-notes-v0.1.0.md
│   └── audit-report.md
├── fixtures/{ocsf,asff,invalid}/
├── scripts/{build_lambda,invoke_local,verify_deployment}
├── src/finding_processor/{adapters,handler,models,triage,idempotency,...}
├── terraform/{root configuration,tests,examples}
├── tests/{unit,integration,security}/
├── README.md, PLAN.md, TASKS.md
├── CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, LICENSE
├── Makefile, pyproject.toml
└── requirements.txt, requirements-dev.txt
```

Generated ZIP files, state, plans, `.tfvars`, `.terraform/`, caches, IDE state, virtual
environments, `.env` files, Terraform CLI credential files, and OS metadata are ignored.
The provider lockfile and sanitized `terraform.tfvars.example` are tracked.

## Terraform implementation

The deployable root under `terraform/` defines only the minimum architecture:

- `aws_cloudwatch_event_rule.findings`: one or two coarse-routing rules according to
  schema mode.
- `aws_cloudwatch_event_target.processor`: direct Lambda targets with retry policy and
  target-delivery DLQ.
- `aws_lambda_permission.eventbridge`: invocation permission restricted to each rule ARN.
- `aws_sqs_queue.eventbridge_dlq`: standard, service-encrypted target DLQ.
- `aws_sqs_queue_policy.eventbridge_dlq`: `sqs:SendMessage` restricted to the intended
  EventBridge service principal and rule ARNs.
- `aws_lambda_function.processor`: Python 3.13, arm64, 256 MB, bounded timeout, packaged
  dependencies, and Powertools configuration.
- `aws_cloudwatch_log_group.processor`: explicit retention.
- `aws_dynamodb_table.idempotency`: on-demand, TTL, service-managed encryption, no
  default PITR because it is ephemeral suppression state rather than an audit database.
- `aws_sns_topic.escalation`: AWS-managed SNS encryption by default; an existing CMK ARN
  can be supplied.
- `aws_iam_role.processor` and inline policy: only own logs, one DynamoDB table, and one
  SNS topic; when an external SNS KMS key is selected, exact data-key/decrypt actions on
  that key are added conditionally.
- Four alarms: Lambda errors, Lambda throttles, visible DLQ messages, and notification
  failures.

The audit corrected the notification-failure alarm to include the Powertools
`service=finding-processor` dimension and changed the Lambda environment from unused
`LOG_LEVEL` to supported `POWERTOOLS_LOG_LEVEL`. `log_level` is now a validated input.
The refresh also prevents `additional_tags` from replacing required project/management
tags.

Terraform does not enable or administer Security Hub, Security Hub CSPM, GuardDuty,
Inspector, Macie, AWS Config, or Organizations. It does not create a backend, S3 bucket,
KMS key, email subscription, ticketing integration, deployment workflow, or remediation
resource.

## Python implementation

- Strict Pydantic envelope/domain validation with bounded normalized fields.
- Dedicated OCSF and ASFF adapters with consistent timestamps and severity handling.
- Unicode-preserving sanitization, control/newline/null removal, account masking, and
  identifier shortening.
- Versioned explainable JSON triage policy with stable decision reason codes.
- Deterministic minimal notification builder that excludes raw descriptions, full
  account IDs, and unnecessary resource identifiers.
- Powertools DynamoDB idempotency key derived from schema family, finding ID, update
  timestamp fallback, and workflow-status fallback.
- Module-scope SNS and DynamoDB clients. Lambda context is registered with Powertools so
  concurrent in-progress locks honor remaining execution time.
- Duplicate responses cannot execute the protected SNS side effect.
- Structured decision logging never serializes the raw event or provider exception text.
- Metric emission failure is safely logged by stable name and does not alter a triage
  decision.
- No command execution, affected-resource retrieval, resource modification, finding
  update, or remediation behavior exists.

## Tests added and strengthened

Python behavior/security coverage includes:

- OCSF and ASFF valid events and all required envelope/cardinality failures.
- Missing IDs/timestamps, invalid timestamps, unknown severity/family, and oversized text.
- Sanitization of control characters, newline/log forging, null bytes, long values,
  account masking, identifiers, and legitimate international Unicode.
- All default triage outcomes and unsupported policy version.
- Stable keys with optional fields, first delivery, exact duplicate, meaningful update,
  concurrent in-progress duplicate, expiration-aware DynamoDB condition, and DynamoDB
  failure using `botocore.stub.Stubber`.
- SNS success/failure, handler-level notification and DynamoDB failure, invalid runtime
  configuration, safe metric degradation, and absence of raw provider details in logs.
- Static checks for complete action SHA pins, forbidden `pull_request_target`, explicit
  workflow permissions, excluded Terraform service enablement, no `local-exec`, version
  consistency, and the real clone URL.

Terraform mocked tests now assert:

- Default, ASFF, dual, and invalid schema modes.
- Invalid log-level rejection.
- Exact event types, runtime, architecture, timeout, environment, retry policy, and DLQ.
- Lambda permission source ARN and EventBridge principal.
- DynamoDB billing, TTL attribute, encryption, and disabled PITR.
- SNS encryption, log retention, required tags, and required alarms.
- DLQ policy principal/action/resource/source restriction.
- Reviewed IAM action sets with no wildcard actions or `Resource = "*"`.

## Security controls

- Least-privilege IAM and source-ARN resource policies.
- Wrong-account provider allowlist input and no hard-coded real account IDs.
- Service-managed encryption defaults with optional existing SNS CMK.
- No raw event logging or storage; bounded normalized data only.
- Sanitized, minimized SNS messages and low-cardinality product normalization.
- Concurrency-safe idempotency, TTL, direct-delivery retry, SQS DLQ, and alarms.
- Explicit processing-error distinction from reject, ignore, duplicate, and delivery
  failure.
- Exact dependency pins, provider lockfile, deterministic artifact, checksum, dependency
  audit, IaC scan, CodeQL, Scorecard, and SHA-pinned actions.
- Read-only workflow permissions by default; no AWS credentials, `pull_request_target`,
  deployment job, or elevated fork execution.
- MIT-0 license recognized by GitHub; substantive source files use SPDX MIT-0 headers.

## CI workflows

- `ci.yml`: Python 3.13 setup, Ruff, mypy, pytest/coverage, Lambda packaging,
  `pip-audit`, Terraform fmt/init/validate/test, TFLint, checksum-pinned Trivy, and
  markdownlint.
- `codeql.yml`: scheduled/push/PR analysis for Python and GitHub Actions.
- `scorecard.yml`: public-repository OpenSSF Scorecard with explicit minimal job
  permissions and SARIF upload.
- Dependabot monitors pip, Terraform, and GitHub Actions weekly.
- Action updates incorporated locally: checkout 7.0.1, setup-python 7.0.0,
  setup-terraform 4.0.1, setup-tflint 6.3.1, and Scorecard 2.4.4. All use immutable
  40-character commit SHAs. CodeQL is pinned to 4.38.2, replacing the v3 line before
  its announced December 2026 deprecation.

No CI or release workflow deploys AWS resources.

## Documentation and decisions

Documentation includes architecture, compatibility, deployment, demo, troubleshooting,
cost/cleanup, security design, threat model, technical research, talk outline, article
outline, GitHub owner settings, release process, prepared release notes, and this audit.

Four ADRs remain intentionally limited to consequential decisions:

1. Security Hub schema strategy.
2. Direct EventBridge-to-Lambda delivery.
3. No automatic remediation.
4. DynamoDB-backed idempotency.

No license ADR, empty support/changelog/notice file, one-resource module hierarchy, or
unsupported optional architecture was added.

## Validation evidence

The current working tree was validated on macOS arm64 with Python 3.13.11 and Terraform
1.16.4. The older deployed sandbox record used Terraform 1.16.0 and remains documented
separately:

- Ruff format/lint: pass.
- Mypy strict: pass, 13 source files.
- Pytest: **60 passed**.
- Overall branch-aware coverage: **95.30%**.
- Adapter modules: 93–96%; sanitization 94%; triage 96%; notifications 100%;
  idempotency 97%.
- Terraform fmt: pass.
- Terraform validate: pass.
- Terraform mocked tests: **7 passed, 0 failed**, no AWS credentials.
- TFLint 0.64.0 with AWS ruleset 0.38.0: pass, no findings.
- Trivy 0.74.0 configuration scan: **0 HIGH/CRITICAL findings**.
- `pip-audit` 2.10.1: no known vulnerabilities in runtime requirements.
- actionlint 1.7.12: all GitHub Actions workflows pass.
- markdownlint-cli2 0.18.1: pass.
- Tracked-artifact and credential-pattern review: no state, plans, private variables,
  build ZIPs, IDE files, or credential-shaped secrets are tracked.
- OCSF and ASFF local demos: pass without AWS credentials.
- Current Lambda package built twice with identical SHA-256:
  `cdad1668fd25d6e2cbec8aa1582b54944a7303c8512c835bf705776e2e3b6aba`.
- The previously deployed/released artifact remains identified by SHA-256
  `b71d666d0601da101e4a80acdad2fe06a09bb7055088150f92b003418f726202`;
  the refresh was not deployed.
- Sandbox Terraform plan/apply created only the intended workflow resources, with no
  changes or destroys; the post-apply plan returned **No changes**.
- Deployed control verifier: Lambda runtime/package, DynamoDB billing/encryption/TTL/PITR,
  SNS encryption/subscriptions, EventBridge target/retry/DLQ, SQS and Lambda resource
  policies, IAM wildcards, log retention, and four alarms: pass.
- Synthetic deployed invocations: first `ESCALATE`, exact duplicate `DUPLICATE`, invalid
  collection `REJECT`; all returned HTTP 200 without Lambda function errors.
- Native SNS metric: one publication for two identical valid invocations.
- CloudWatch logs: structured decisions/rejection and six expected EMF workflow metrics;
  raw fixture title, description, and resource identifier absent.
- Subsequent Security Hub onboarding window: AWS-owned findings were received and
  validated, with `ESCALATE`, `RECORD`, and `IGNORE` decisions and no observed Lambda
  errors, throttles, notification failures, or visible DLQ messages. Exact counts are
  omitted because they are account-specific telemetry, not a reproducible benchmark.

## Scanner suppression

One narrow inline Trivy suppression exists in `terraform/notifications.tf`:

- `AWS-0136`: customer-managed SNS encryption key.
- Rationale: the reference deliberately uses `alias/aws/sns` by default to avoid CMK
  cost, service-principal/key-policy complexity, deletion lifecycle, and accidental loss
  of notification access. Users can provide an existing CMK ARN. The decision and its
  tradeoffs are documented; the scanner is not disabled globally.

No other scanner suppression was added.

## Commands executed

The audit executed non-deployment commands including:

```text
git status --short --branch
git ls-files
make setup
make check
make lint
make typecheck
make test
make package (twice)
make demo-local-ocsf
make demo-local-asff
make markdown
terraform 1.16.4 init -backend=false -upgrade
terraform fmt -recursive
terraform validate
terraform test
terraform plan -out=<ignored-plan>
terraform apply <reviewed-plan> # authorized sandbox deployment
python scripts/verify_deployment.py <deployed outputs>
aws lambda invoke <synthetic OCSF fixture> # first delivery and exact duplicate
aws lambda invoke <synthetic invalid fixture>
tflint --init
tflint --recursive
trivy config --exit-code 1 --severity HIGH,CRITICAL terraform
python -m pip_audit -r requirements.txt
```

Terraform, TFLint, and Trivy binaries were obtained from their official releases and
verified against published SHA-256 checksums before execution. Official GitHub release
tags/API metadata were used to resolve refreshed Actions to complete commit SHAs. The
earlier authenticated GitHub work merged PR #15, enabled repository controls, and closed
obsolete Dependabot PRs. The earlier AWS apply was explicitly authorized and used the
saved reviewed plan; the 2026-09-26 refresh made no AWS API call.

## Known limitations

- Live AWS-owned delivery was validated only in one sandbox account and `us-east-1`; it
  does not establish multi-account, cross-Region, or production behavior.
- Event schemas can evolve; the bounded adapters require maintenance and fixture updates.
- Dual mode does not correlate semantically equivalent OCSF and ASFF findings.
- EventBridge target DLQ does not capture application errors after successful invocation.
- No Lambda asynchronous-failure destination is configured; alarms and logs expose those
  errors for operator action.
- Severity-based triage lacks business/environment context and must not be equated with
  organizational risk.
- Notification-flood and cost controls require account-specific operational thresholds.
- Region, aggregation, administrator/member, and integration availability remain manual
  prerequisites.
- The verification helper remains a read-only control check; end-to-end delivery was
  established separately through observed EventBridge, Lambda, and workflow telemetry.
- This is an educational reference, not production-ready, certified, or compliant.

## Optional features not implemented

No optional S3 decision records, generated customer-managed KMS keys, finding updates,
GuardDuty sample generation, Security Hub CSPM custom import, dashboard, multi-account
routing, cross-Region example, ticketing, Step Functions, Systems Manager Automation,
GitHub OIDC deployment, or automated remediation is implemented.

## Manual deployment prerequisites

- An explicitly authorized account and supported Region.
- The selected Security Hub capability already enabled and producing findings.
- An authenticated least-privilege AWS identity and a non-empty intended account
  allowlist.
- A reviewed Lambda package and Terraform plan.
- Local state only for a personal demo, or an existing separately governed S3 backend
  with versioning, encryption, least privilege, and S3 lockfile locking.
- Explicit cost/account-impact approval, operational notification ownership, and cleanup
  plan.

Terraform does not enable or disable pre-existing account-level security services.

## Repository-host status

At the 2026-08-29 authenticated verification, GitHub recognized MIT-0, the repository had
a description and topics, `main` required pull requests and the five critical GitHub
Actions checks, force pushes/deletion were blocked, and linear history was required.
Secret scanning, push protection, Dependabot alerts/security updates, automated security
fixes, and private vulnerability reporting were enabled. These are host-side controls,
so `docs/github-repository-settings.md` treats them as a dated snapshot and recheck
checklist rather than a timeless repository claim.

The annotated `v0.1.0` tag and public GitHub Release were created from the fully green
release commit. The release is neither a draft nor a prerelease. Exact settings and the
repeatable release process are in `docs/github-repository-settings.md` and
`docs/release-process.md`.

## Safety confirmations

- No `terraform destroy`, attack generation, or remediation command was run. Security Hub
  enablement occurred outside this Terraform stack and repository automation.
- An explicitly authorized sandbox apply created the intended workflow resources; ignored
  local state records them and must be preserved until cleanup.
- The sandbox post-apply plan returned `No changes`; the DLQ was empty and no SNS
  subscription existed.
- No AWS credential, static secret, full account identifier, or real finding is committed.
- No attack, vulnerable infrastructure, account-level security-service enablement, or
  remediation was generated.
- Only repository-owned synthetic fixtures were invoked directly. Security Hub was later
  enabled outside this Terraform stack, after which AWS-owned OCSF findings traversed the
  deployed path. No attack or vulnerable resource was generated for that validation.
  Exactly one SNS publication occurred for the two identical direct synthetic
  invocations, and raw fixture text was absent from inspected logs.
- PRs #15 and #17 were committed, pushed, checked, and squash-merged. GitHub repository
  settings were hardened, and the annotated `v0.1.0` tag and public Release were created.
