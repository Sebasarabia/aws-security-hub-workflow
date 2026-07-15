# ADR 0004: DynamoDB-backed idempotency

Status: Accepted

## Context

Event-driven systems deliver at least once; duplicate notification can create fatigue.

## Decision

Use Powertools DynamoDB idempotency with a stable key derived from schema family,
finding ID, update time, and workflow status. Use on-demand billing, TTL, and
service-managed encryption. PITR is off by default because this is ephemeral state.

## Alternatives considered

In-memory caches do not span environments. SNS FIFO is not a universal notification
substitute. A custom conditional-write implementation duplicates Powertools behavior.

## Consequences

Exact deliveries are suppressed, meaningful updates are processed again, and concurrent
execution is locked. DynamoDB is a runtime dependency and this table is not an audit DB.

## Security implications

The role receives only item-level actions on one table. TTL bounds retention and cost.

