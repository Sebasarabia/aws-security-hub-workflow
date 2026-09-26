# Demo runbook

Target: six minutes, leaving margin under the eight-minute talk limit.

## Validated deployed path

Use only pre-reviewed, sanitized evidence; do not wait for a new finding during the talk:

1. Show the EventBridge rule source and `Findings Imported V2` detail type.
2. Show CloudWatch decision records containing only schema family, decision, reason code,
   normalized product, masked account, and correlation ID.
3. Show aggregate workflow metrics and the healthy Lambda/DLQ alarms without quoting
   account-specific counts as a benchmark.
4. Explain that SNS had no repository-created subscription and that no affected resource
   was modified.

State that this proves AWS-owned finding delivery through one account and Region, not an
attack, confirmed incident, production-readiness claim, or universal regional result.
Never display raw findings, full identifiers, account IDs, or notification payloads.

## Deterministic local path and contingency

1. State that all local fixtures are invented and synthetic.
2. Run `make demo-local-ocsf`; point out one sanitized notification payload and
   `ESCALATE`.
3. Demonstrate duplicate behavior through
   `tests/integration/test_handler.py::test_ocsf_escalation_and_duplicate`; no second
   notification occurs.
4. Run `make demo-local-asff`; explain that the ASFF adapter is compatibility only.
5. Show `config/triage-policy.json`, the EventBridge patterns, and the no-remediation IAM
   policy.

The local demo exercises validation, adapters, sanitization, triage, process-local
idempotency semantics, notification construction, logs, and metric serialization. It
does **not** exercise EventBridge delivery, regional integration, IAM, or DynamoDB's
concurrency protocol. Use it as the default reproducible path and as the offline fallback.
