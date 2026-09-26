# Task tracker

SPDX-License-Identifier: MIT-0

| Phase | Task | Status | Validation | Notes |
|---|---|---|---|---|
| 0 | Primary-source reconciliation | Complete | Review `docs/research-notes.md` | Initial review 2026-08-29; focused refresh 2026-09-26 |
| 0 | Architecture, ADRs, threat model | Complete | Markdown review | Required scope only |
| 1 | Models, adapters, sanitization, triage | Complete | `make test` | EventBridge envelope and behavior tests exceed coverage thresholds |
| 1 | Idempotency, notification, handler, fixtures | Complete | `make test` | Powertools DynamoDB path and failures tested without AWS |
| 2 | Terraform resources and IAM | Complete | `make terraform-validate` | Authorized sandbox deployment validated separately |
| 2 | Terraform mocked tests | Complete | `make terraform-test` | Seven IAM, routing, storage, alarms, KMS, and tag scenarios; no AWS credentials |
| 3 | CI and governance | Complete | Ruff, mypy, TFLint, Trivy, pip-audit | SHA-pinned actions |
| 3 | Documentation and outlines | Complete | `make markdown` | Repository Markdown passes the configured rules |
| 3 | Reproducible Lambda package | Complete | `make package` twice | Identical SHA-256 checksums |
| 3 | Dependency refresh | Complete | `make setup`, `pip-audit` | Runtime, development tools, Actions, and provider lock refreshed 2026-09-26 |
| 3 | v0.1.0 release publication | Complete | GitHub Release and tag verification | PRs #15/#17 merged; annotated tag and public release published |
| 3 | GitHub protection, metadata, security settings | Complete | `docs/github-repository-settings.md` | Controls verified on the recorded date; recheck after platform changes |
| 3 | AWS sandbox validation | Complete | `docs/deployment-validation.md` | Infrastructure, synthetic behavior, and AWS-owned OCSF delivery verified |
| 3 | Presentation material | Complete for repository | `docs/talk-outline.md` | Talk outline and safe demo runbook are maintained in the repository |
| 3 | Public-record review | Complete | Secret/privacy scan and Markdown checks | Account-specific telemetry and local profile details omitted |
| 4 | Optional integrations | Not planned | N/A | Required scope first; omitted in v1 |
