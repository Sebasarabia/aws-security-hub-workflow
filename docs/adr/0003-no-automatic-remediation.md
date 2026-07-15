# ADR 0003: No automatic remediation

Status: Accepted

## Context

Findings are untrusted signals, and severity alone does not capture business context.

## Decision

V1 only validates, classifies, suppresses duplicates, records decisions, and sends a
minimal notification recommending manual review.

## Alternatives considered

Resource isolation, credential revocation, IAM mutation, deletion, and SSM Automation
were rejected for v1. Approval-based automation may be considered later.

## Consequences

The project is safe to teach and cannot itself contain an incident. Response remains a
human operational responsibility.

## Security implications

The role has no affected-resource permissions. A spoofed or mistaken finding cannot
cause destructive resource changes.

