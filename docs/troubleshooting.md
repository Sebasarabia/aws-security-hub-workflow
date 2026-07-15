# Troubleshooting

- `SCHEMA_MODE_REJECTED`: event family differs from configured mode; inspect the two
  exact detail types and use `dual` only deliberately.
- `event_must_contain_exactly_one_finding`: the documented contract was not met; do not
  weaken validation. Capture only sanitized structural diagnostics.
- EventBridge DLQ message: delivery to Lambda failed. Inspect message attributes such as
  rule/target ARN and error code, repair permission/target issues, then replay manually.
- Lambda `Errors`/`ProcessingErrors`: invocation arrived but application/downstream work
  failed. The target DLQ does not represent this path.
- No SNS delivery: confirm decision is `ESCALATE`, then inspect topic subscriptions,
  endpoint confirmation, topic/key policy, and `NotificationFailures` without copying
  raw findings.
- Duplicates: exact updates are suppressed within TTL; changed `updated_at` or workflow
  status is intentionally a new key. Dual mode can create semantic duplicates.
- Terraform account guard: replace the placeholder with the intended 12-digit account;
  never remove the guard merely to make deployment proceed.

