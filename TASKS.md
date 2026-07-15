# Task tracker

SPDX-License-Identifier: MIT-0

| Phase | Task | Status | Validation | Notes |
|---|---|---|---|---|
| 0 | Primary-source reconciliation | Complete | Review `docs/research-notes.md` | Verified 2026-07-13 |
| 0 | Architecture, ADRs, threat model | Complete | Markdown review | Required scope only |
| 1 | Models, adapters, sanitization, triage | Complete | `make test` | 43 passed; 90.30% coverage |
| 1 | Idempotency, notification, handler, fixtures | Complete | `make demo-local-ocsf` | No AWS credentials |
| 2 | Terraform resources and IAM | Complete | `make terraform-validate` | No apply |
| 2 | Terraform mocked tests | Complete | `make terraform-test` | 4 passed, no AWS credentials |
| 3 | CI and governance | Complete | Ruff, mypy, TFLint, Trivy, pip-audit | SHA-pinned actions |
| 3 | Documentation and outlines | Complete | markdownlint-cli2 | 25 files, no errors |
| 3 | Reproducible Lambda package | Complete | `make package` twice | Identical SHA-256 checksums |
| 4 | Optional integrations | Not planned | N/A | Required scope first; omitted in v1 |
