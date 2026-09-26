# Task tracker

SPDX-License-Identifier: MIT-0

This is the retained phase summary, not a live issue tracker. Current verification
evidence belongs in `docs/audit-report.md`.

| Phase | Scope | Status | Primary validation |
|---|---|---|---|
| 0 | Research, architecture, ADRs, threat model | Complete | `docs/research-notes.md` and `docs/adr/` |
| 1 | Python workflow, adapters, policy, idempotency, fixtures | Complete | `make test` |
| 2 | Terraform, IAM, routing, storage, alarms | Complete | `make terraform-validate terraform-test` |
| 3 | CI, packaging, security checks, documentation | Complete | `make check` |
| 3 | Sanitized sandbox and AWS-owned OCSF validation | Complete | `docs/deployment-validation.md` |
| 3 | Presentation and reproducible demo material | Complete | `docs/talk-outline.md` and `docs/demo-runbook.md` |
| 4 | Optional integrations | Not planned for version 1 | See `README.md` limitations |
