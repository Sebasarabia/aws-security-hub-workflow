# ADR 0001: Security Hub schema strategy

Status: Accepted

## Context

Current Security Hub emits OCSF 1.6 `Findings Imported V2`; Security Hub CSPM emits
ASFF `Security Hub Findings - Imported`. Their field names and semantics differ.

## Decision

Default to OCSF, allow `asff` and `dual`, isolate source fields in separate adapters,
and converge on a small normalized model. Dual is only a teaching/migration mode.

## Alternatives considered

ASFF-only would center the compatibility path. A union model would leak source fields
into policy logic. Converting the entire schemas would add unused complexity.

## Consequences

Business logic is stable and testable, but adapters need maintenance as schemas evolve.
Dual deployments can receive logically duplicated signals.

## Security implications

Every event is revalidated regardless of source. Raw events are not retained or logged.

