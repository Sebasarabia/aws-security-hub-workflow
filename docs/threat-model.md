# Threat model

Assets are findings, AWS accounts, the Lambda role, SNS topic, DynamoDB table, Terraform
state, workflows, source, lockfiles, deployment artifact, and operational records.
Boundaries are Security Hub→EventBridge, EventBridge→Lambda, Lambda→AWS APIs, local
developer tools, Terraform state, and a possible future GitHub→AWS OIDC relationship.
Likelihood is qualitative and context-dependent; no numeric risk score is implied.

| Threat | Likelihood / impact | Mitigation | Detection | Residual risk / control |
|---|---|---|---|---|
| Malformed finding | High / Medium | Pydantic, envelope/adapters, bounds | Rejected metric/log | Schema drift; adapter tests |
| Spoofed/direct invocation | Medium / Medium | AWS-owned source pattern, Lambda source-ARN permission, full payload validation | source/reject records | A separately privileged principal could invoke Lambda directly; IAM governance |
| Duplicate/replay | High / Medium | Powertools DynamoDB key, TTL, concurrency lock | Duplicate metric | Semantic cross-schema duplicates; dual warning |
| Log injection | Medium / Medium | Remove controls/newlines, structured fields, no raw event | log review | Unicode visual ambiguity; sanitization tests |
| Sensitive leakage | Medium / High | minimization, masking, no raw log/S3, short SNS | notification/log review | titles may still be sensitive; field limits/tests |
| Excessive IAM | Medium / High | Resource-scoped API access; EMF avoids a metric wildcard | Terraform test/Trivy | Future features can widen access; IAM review |
| Wrong-account deploy | Medium / High | provider account allowlist | plan identity review | empty default allows validation; deployment checklist |
| Terraform state exposure | Medium / High | ignore locally; existing encrypted/versioned S3 and lockfile | repo/CloudTrail review | backend operator access; deployment guide |
| Compromised dependency | Medium / High | exact pins, pip-audit, Dependabot, packaged checksum | CI advisories | zero-days; requirements/CI |
| Compromised Action | Medium / High | full SHA pins, read-only tokens, Dependabot | Scorecard/CodeQL | maintainer/repository compromise; workflows |
| PR token abuse | Medium / High | no `pull_request_target`, no AWS secrets, explicit permissions | workflow audit | malicious code uses runner resources; CI design |
| Notification flooding | Medium / Medium | policy plus idempotency; no auto-subscription | metrics/SNS and cost alarms | many unique findings; operational thresholds |
| Cost abuse | Low / Medium | on-demand/TTL, retention, alarms, minimal services | billing/anomaly tooling | extreme event volume; owner governance |
| Synthetic/real confusion | Medium / Medium | explicit flags, invented IDs, runbook wording | decision fields | presenter error; demo review |
| Accidental remediation | Low / High | no code, target access, or IAM permissions | policy/IaC review | future changes; ADR and tests |
| Delivery failure | Medium / Medium | bounded retry and target DLQ | DLQ/error alarms | manual replay required; operations docs |
| Application failure | Medium / Medium | safe exception, Lambda/custom alarms | error/processing metrics | EventBridge DLQ does not capture it; troubleshooting |
