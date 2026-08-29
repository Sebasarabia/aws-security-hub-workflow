# GitHub repository settings

SPDX-License-Identifier: MIT-0

These settings are part of the repository's security boundary but are not stored in
Git. They require repository-owner access and must be verified after material GitHub
platform changes. This document is a configuration checklist, not evidence that a
setting has been enabled.

## Repository metadata

Use the following public metadata:

- Description: `Educational AWS Security Hub workflow using Terraform, EventBridge,
  Python Lambda, DynamoDB idempotency, and SNS.`
- Website: leave empty until the presentation or article has a stable public URL.
- Topics: `aws`, `aws-security`, `security-hub`, `security-hub-cspm`, `ocsf`,
  `terraform`, `python`, `eventbridge`, and `lambda`.
- Features: Issues enabled; Wiki and Discussions disabled unless there is a maintained
  use case. Projects is optional.

## Active ruleset for `main`

Create an active branch ruleset targeting the default branch with:

- Restrict deletions.
- Block force pushes.
- Require a pull request before merging.
- Require all conversations to be resolved.
- Require the branch to be up to date before merging.
- Require these uniquely named checks:
  - `CI / python`
  - `CI / terraform`
  - `CI / markdown`
  - `CodeQL / analyze (python)`
  - `CodeQL / analyze (actions)`
- Do not require OpenSSF Scorecard as a pull-request check because its workflow runs on
  push, schedule, and branch-protection changes rather than pull requests.
- For a single-maintainer repository, zero required external approvals is acceptable
  initially. Increase to one approval when another trusted maintainer is available.
- Do not configure routine bypass actors. Repository administrators can edit an
  incorrect ruleset through Settings; bypass should not be the normal merge path.

Requiring signed commits and linear history are reasonable follow-up controls after the
maintainer has tested local signing, Dependabot, and the chosen GitHub merge method.

## Security and quality

Under **Settings → Security and quality → Advanced Security**, verify:

- Dependency graph enabled.
- Dependabot alerts enabled.
- Dependabot security updates enabled.
- Secret scanning enabled. Public repositories receive supported scanning features,
  but the visible repository setting and alert queue should still be reviewed.
- Push protection enabled where offered, with bypasses reviewed rather than ignored.
- Private vulnerability reporting enabled and maintainer security-alert notifications
  configured. `SECURITY.md` intentionally directs researchers to this private path.
- CodeQL default/setup status has no duplicate configuration competing with
  `.github/workflows/codeql.yml`.

Under **Settings → Actions → General**:

- Keep default `GITHUB_TOKEN` permissions read-only.
- Do not allow GitHub Actions to create and approve pull requests.
- Permit only the actions required by the committed workflows, or require complete SHA
  pins if that repository-level policy is available.
- Never add repository AWS access keys. A future deployment workflow must use OIDC and
  a protected environment, as described in `docs/deployment.md`.

## Release publication

Before publishing `v0.1.0`, verify the ruleset and security settings above, merge the
reviewed change through a pull request, and confirm all required checks on the exact
release commit. Follow `docs/release-process.md`; do not create or reuse a tag before the
commit is final.

## Verification record

Record the review date, reviewer, ruleset name, enabled checks, unresolved security
alerts, and release URL in `docs/audit-report.md` or the release issue. Screenshots are
optional operational evidence and should not contain tokens, account details, or other
sensitive browser data.

Official guidance:

- [Available rules for GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub Actions secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub security features](https://docs.github.com/en/code-security/getting-started/github-security-features)
- [Private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)
