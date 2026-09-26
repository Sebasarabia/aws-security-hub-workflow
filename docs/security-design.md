# Security design

This is a reference implementation informed by selected AWS, NIST, and OWASP practices;
it makes no certification, compliance, or production-readiness claim.

## Boundaries and data minimization

Findings are untrusted across Security Hub→EventBridge and EventBridge→Lambda. Lambda's
execution role is the boundary to DynamoDB, SNS, and CloudWatch. Local developer state,
Terraform state, the build artifact, and future GitHub OIDC are supply/deployment
boundaries. Event source and detail type are coarse hints, never proof of trust.

The handler requires a complete envelope and exactly one finding, then uses a dedicated
adapter. Only fields required for triage survive normalization. Control characters and
newlines are removed while Unicode is retained; lengths are bounded; accounts and
resource/finding identifiers are masked or shortened. Raw events and full descriptions
are not logged, notified, or copied to S3. Security Hub retains the underlying finding.

## Triage, idempotency, and failures

The versioned policy yields a decision and machine reason code. Severity is a routing
example, not organizational risk. Powertools creates concurrency-safe DynamoDB records
from stable finding/update fields; TTL bounds ephemeral state. The table is not an audit
database. EventBridge retries target delivery and sends exhausted delivery failures to
the same-Region DLQ. A Lambda error after successful invocation is instead observed by
Lambda error/custom metrics. Malformed input is `REJECT`, an intentional policy outcome
can be `IGNORE`, and neither is silently converted into a processing failure.

## IAM, encryption, and notifications

EventBridge Lambda permission and SQS policy are restricted to rule ARNs. The Lambda role
has log-stream writes for its group, item operations for one table, publish to one topic,
and no affected-resource or IAM mutation permissions. Powertools emits custom metrics in
Embedded Metric Format through the existing log stream, so the role does not need the
otherwise wildcard-scoped `cloudwatch:PutMetricData` permission.

DynamoDB/SQS use service-managed at-rest encryption and SNS uses `alias/aws/sns` by
default. An existing customer-managed SNS key is optional. When supplied, Terraform grants
the processor the exact symmetric data-key actions and `kms:Decrypt` only on that key;
the operator must also maintain a compatible key policy. A CMK adds charges, policy and
complexity, rotation/deletion lifecycle, and risk of making messages unavailable. No key
is created just for appearance. SNS contains minimal operational context and no automatic
subscription.

S3 raw storage is excluded because it duplicates sensitive data without a v1 requirement.
Future decision records should contain only normalized/sanitized outcomes and must not be
described as legal evidence or chain-of-custody. Automated remediation is excluded because
signals can be malformed, duplicated, incomplete, or lack business context.

## Standards alignment

- AWS Well-Architected Security Pillar outcomes inform least privilege, traceability,
  data protection, and preparation. AWS SRA informs the gradual multi-account path.
  Lambda, IAM, Security Hub, and EventBridge documentation drives service controls.
- NIST CSF 2.0 informs Govern/Identify/Detect/Respond framing; SP 800-61r3 informs
  preparation and triage; SSDF 1.1 informs reviewed, tested, dependency-aware delivery.
- OWASP IaC, CI/CD, and Software Supply Chain cheat sheets inform scanning, pinned
  automation, dependency auditing, artifact integrity, and secret avoidance.
