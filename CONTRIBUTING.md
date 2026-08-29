# Contributing

Contributions are welcome through reviewed pull requests. By contributing, you agree
that your contribution is licensed under MIT-0 and follows the code of conduct.

Use Python 3.13. Run `make setup` once; it also runs `pip check` after installation. The
commands are intentionally transparent:

- `make format`: Ruff formatting/fixes and `terraform fmt`.
- `make lint`, `make typecheck`, `make test`: Ruff, strict mypy, and pytest coverage.
- `make package`: clean Linux arm64 dependency install, source copy, deterministic zip,
  SHA-256 checksum. The build directory is ignored.
- `make terraform-init`: `terraform init -backend=false`.
- `make terraform-fmt`, `make terraform-validate`, `make terraform-test`: static/native tests;
  mocked tests need no AWS credentials.
- `make security`: pip-audit plus one IaC scanner, Trivy.
- `make markdown`: markdownlint-cli2.
- `make check`: all non-deployment quality checks.

Add behavior-focused tests. Never add real findings, accounts, credentials, state, plan
files, build archives, active deployment workflows, account-level service enablement,
or remediation permissions. Update research notes when contracts or versions change.
Do not run `terraform apply` as part of contribution validation.
