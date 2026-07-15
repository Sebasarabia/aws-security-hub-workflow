# Demo runbook

Target: six minutes, leaving margin under the eight-minute talk limit.

1. State that all local fixtures are invented and synthetic.
2. Run `make demo-local-ocsf`; point out one sanitized SNS payload and `ESCALATE`.
3. Run it again in one process when demonstrating duplicate behavior through tests, or
   show `tests/integration/test_handler.py`; no second notification occurs.
4. Run `make demo-local-asff`; explain that the ASFF adapter is compatibility only.
5. Show `config/triage-policy.json`, then the EventBridge patterns and DLQ.
6. Show tests and the no-remediation IAM policy.

The local demo exercises validation, adapters, sanitation, triage, local idempotency
semantics, notification construction, logs, and metrics serialization. It does **not**
exercise AWS delivery, Security Hub enablement, regional integration, IAM, or the real
DynamoDB concurrency protocol. A deployed demo requires pre-existing service enablement
and is a workflow test, not proof that a synthetic signal is a real incident.

