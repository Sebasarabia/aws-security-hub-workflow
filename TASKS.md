# Task tracker

SPDX-License-Identifier: MIT-0

| Phase | Task | Status | Validation | Notes |
|---|---|---|---|---|
| 0 | Primary-source reconciliation | Complete | Review `docs/research-notes.md` | Refreshed 2026-08-29 |
| 0 | Architecture, ADRs, threat model | Complete | Markdown review | Required scope only |
| 1 | Models, adapters, sanitization, triage | Complete | `make test` | 54 passed; 96.07% coverage |
| 1 | Idempotency, notification, handler, fixtures | Complete | `make test` | Powertools DynamoDB path and failures tested without AWS |
| 2 | Terraform resources and IAM | Complete | `make terraform-validate` | No apply |
| 2 | Terraform mocked tests | Complete | `make terraform-test` | 5 passed, stronger IAM/alarms, no AWS credentials |
| 3 | CI and governance | Complete | Ruff, mypy, TFLint, Trivy, pip-audit | SHA-pinned actions |
| 3 | Documentation and outlines | Complete | markdownlint-cli2 | 29 files, no errors |
| 3 | Reproducible Lambda package | Complete | `make package` twice | Identical SHA-256 checksums |
| 3 | Dependency refresh | Complete | `make setup`, `pip-audit` | Corrected incompatible Dependabot Pydantic Core pin |
| 3 | v0.1.0 release preparation | Complete locally | Review release docs | No tag, release, commit, or push performed |
| 3 | GitHub ruleset, metadata, security settings | Owner action | `docs/github-repository-settings.md` | Requires authenticated repository administration |
| 4 | Optional integrations | Not planned | N/A | Required scope first; omitted in v1 |
