# Architecture

The minimum architecture is intentionally direct: two optional event families, separate
rules, one Lambda, one ephemeral idempotency table, one SNS topic, one target-delivery
DLQ, and CloudWatch observability. Every resource has a named runtime purpose.

```text
OCSF event ─> OCSF adapter ─┐
                            ├─> normalized finding ─> sanitize ─> triage
ASFF event ─> ASFF adapter ─┘                                  │
                          EventBridge delivery failure ─> DLQ   ├─> idempotency
                                                               ├─> decision log/metrics
                                                               └─> minimal SNS (ESCALATE)
```

Direct delivery suits one quick consumer and a teaching workflow. Insert an SQS queue
before Lambda for sustained bursts, downstream backpressure, independent consumption,
multiple consumers, or more explicit replay. That changes operational semantics and
needs its own redrive, visibility-timeout, batch, and partial-failure design.

Standalone adoption starts with one account and Region. Evolution can route member
accounts to a delegated security account, introduce aggregation Regions deliberately,
and operate regional processors. Version 1 configures none of those relationships.

