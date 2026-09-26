# Technical reconciliation notes

SPDX-License-Identifier: MIT-0

Initial verification: **2026-08-29**. Focused version/provider recheck:
**2026-09-26**. Sources were limited to the authoritative sources requested for this
project. The notes paraphrase rather than reproduce the sources.

## Terminology and event contracts

- Current **AWS Security Hub** is a unified service that consumes and generates OCSF
  findings. AWS documents OCSF schema version 1.6. Its EventBridge detail type is
  exactly `Findings Imported V2`, source `aws.securityhub`, and `detail.findings`
  contains exactly one OCSF finding.
- **AWS Security Hub CSPM** remains the posture-management capability and ASFF path.
  Its detail type is exactly `Security Hub Findings - Imported`, also from
  `aws.securityhub`; the event contains exactly one ASFF finding.
- These names are intentionally separate in code and documentation. `dual` is a
  migration/teaching mode and can process logically duplicated signals.

## Versions selected

- Terraform current stable: **1.16.4**. Configuration range: `>= 1.10.0, < 2.0.0`.
  The lower bound retains native mocked-provider tests and is the tested policy floor.
- HashiCorp AWS Provider current: **6.66.0**. Configuration range: `>= 6.54.0, < 7.0.0`;
  the lockfile selects 6.66.0. Terraform 1.16.4 installed this signed release directly
  from the Registry during verification.
- Lambda Python runtimes currently include stable Python 3.10 through 3.14. Python 3.15
  is public preview and is not covered by the Lambda SLA or Technical Support.
  **Python 3.13** remains selected: it runs on Amazon Linux 2023, is supported into
  2029, and is compatible with all pinned dependencies. A preview runtime is not
  appropriate for this reference.
- Powertools for AWS Lambda (Python) **3.35.0** is selected. Its official release and
  current documentation retain Logger, EMF Metrics, Pydantic-based validation, and
  DynamoDB idempotency capabilities used here.
- Runtime pins were refreshed to Boto3 1.43.103 and Pydantic 2.13.5. Dependency
  resolution confirms Pydantic Core 2.46.5 as the compatible exact pin.
- Runtime dependencies are exact-pinned in `requirements.txt`, including Boto3.
  The runtime-provided SDK is not relied upon.

## Terraform support

AWS Provider 6.66.0 supports the standard resources proposed here:
`aws_cloudwatch_event_rule`, `aws_cloudwatch_event_target`, `aws_lambda_function`,
`aws_lambda_permission`, `aws_iam_role`, `aws_iam_role_policy`,
`aws_dynamodb_table`, `aws_sns_topic`, `aws_sqs_queue`, `aws_sqs_queue_policy`,
`aws_cloudwatch_log_group`, and `aws_cloudwatch_metric_alarm`. No unsupported
resource is required. AWS Provider 6.66.0 also supports
`aws_securityhub_account_v2`, but it is deliberately excluded: Security Hub has an
account/Regional lifecycle and cost boundary independent of this workflow, and
destroying that Terraform resource disables Security Hub V2. The classic
`aws_securityhub_account` resource manages Security Hub CSPM, not the current unified
Security Hub. The deployment artifact must be built before planning; Terraform does not
install Python dependencies.

## Regional availability and limitations

- Security Hub and Security Hub CSPM are Regional and available in most, not all,
  Regions. Endpoint lists and capability/integration/control availability must be
  checked immediately before deployment. The reference defaults to `us-east-1` but
  makes no universal-Region claim.
- Security Hub CSPM only receives/processes findings in Regions where it is enabled.
  Cross-Region aggregation has partition and opt-in-Region limitations, and individual
  integrations/controls vary by Region.
- EventBridge's target DLQ must be an SQS **standard** queue in the same Region as the
  rule. The queue policy must grant `events.amazonaws.com` `sqs:SendMessage` only when
  `aws:SourceArn` is one of the intended rules.
- The Security Hub feed of an administrator or aggregation Region can include member
  and linked-Region findings. This reference does not configure those relationships.

## Powertools and GitHub Actions

Powertools for AWS Lambda (Python) provides JSON Logger, EMF Metrics, and DynamoDB
idempotency with concurrent in-progress protection and configurable expiry. Its
default table key and TTL fields are `id` and `expiration`; those are used here.
AWS recommends clients outside handlers, idempotent code, structured JSON logging,
and asynchronous EMF metrics.

GitHub recommends least-privilege explicit `GITHUB_TOKEN` permissions and complete
commit-SHA pins because a full SHA is the immutable action reference. CI does not use
`pull_request_target`, AWS credentials, or elevated fork permissions. Dependabot
covers Actions and pip. A future deployment workflow should use OIDC and a protected
environment; none is active in version 1.

As refreshed on 2026-09-26, the SHA-pinned actions are checkout 7.0.1, setup-python
7.0.0, setup-terraform 4.0.1, setup-tflint 6.3.1, OpenSSF Scorecard 2.4.4, and CodeQL
4.38.2. CodeQL v4 replaces the still-supported but December 2026-deprecated v3 line.
Version comments match the immutable commits resolved from official GitHub release tags.
Branch protection, secret scanning, push protection, Dependabot alerts/security updates,
and private vulnerability reporting were enabled and verified through the authenticated
GitHub API on 2026-08-29. Their intended configuration is recorded separately.

The March 2026 Trivy supply-chain incident affected mutable action/setup tags. CI
therefore avoids the Trivy GitHub Action and installs standalone Trivy 0.74.0 after
checking a hard-coded release SHA-256. This does not eliminate upstream risk, but it
removes mutable action indirection and makes the consumed binary explicit.

## Assumptions and uncertainties

- OCSF has multiple finding classes and optional shapes. The adapter validates only
  the bounded fields needed by the workflow and accepts documented timestamp variants.
- Source product normalization uses a small allowlist and `OTHER`, preventing metric
  cardinality from untrusted names.
- Severity alone is a routing demonstration, not organizational risk measurement.
- Provider docs are JavaScript-rendered; the Registry release page and installed
  provider schema during `terraform init` are the final validation authorities.
- Account ownership metadata was not available, so the license names repository
  contributors rather than AWS or an individual.

## Official references

- [Terraform releases](https://releases.hashicorp.com/terraform/)
- [AWS Provider Registry](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWS Provider 6.66.0 release](https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.66.0)
- [Terraform `aws_securityhub_account_v2` resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/securityhub_account_v2)
- [Terraform provider requirements and lockfiles](https://developer.hashicorp.com/terraform/language/providers/requirements)
- [Terraform mocked tests](https://developer.hashicorp.com/terraform/language/tests/mocking)
- [S3 backend and S3 lockfiles](https://developer.hashicorp.com/terraform/language/backend/s3)
- [Lambda supported runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [Lambda Python runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Introduction to Security Hub](https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub-v2.html)
- [Introduction to Security Hub CSPM](https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html)
- [Security Hub and OCSF](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-ocsf.html)
- [Security Hub V2 EventBridge event types](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-v2-cwe-event-types.html)
- [Security Hub V2 EventBridge format](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-v2-cwe-event-formats.html)
- [Security Hub CSPM EventBridge format](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-cwe-event-formats.html)
- [Security Hub CSPM regional limits](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-regions.html)
- [Security Hub CSPM endpoints](https://docs.aws.amazon.com/general/latest/gr/sechub.html)
- [EventBridge retry policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html)
- [EventBridge target DLQs](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html)
- [SNS key management](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html)
- [Powertools Python documentation](https://docs.powertools.aws.dev/lambda/python/latest/)
- [Powertools Python 3.35.0 release](https://github.com/aws-powertools/powertools-lambda-python/releases/tag/v3.35.0)
- [GitHub Actions secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [CodeQL Action changelog](https://github.com/github/codeql-action/blob/main/CHANGELOG.md)
- [GitHub ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)
- [Trivy 2026 security advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/introduction.html)
- [NIST CSF 2.0](https://www.nist.gov/cyberframework)
- [NIST SP 800-61 Revision 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
- [OWASP IaC Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html)
- [OWASP CI/CD Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html)
- [OWASP Software Supply Chain Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Software_Supply_Chain_Security_Cheat_Sheet.html)
