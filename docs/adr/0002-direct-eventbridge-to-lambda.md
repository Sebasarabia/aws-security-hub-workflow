# ADR 0002: Direct EventBridge to Lambda

Status: Accepted

## Context

The educational v1 has one fast consumer and no demonstrated sustained burst or replay
requirement.

## Decision

Route rules directly to Lambda with bounded retry/event age and an SQS target DLQ.

## Alternatives considered

SQS buffering and EventBridge Pipes improve backpressure and independent replay but
add resources and a second delivery contract. Step Functions is unnecessary here.

## Consequences

The flow is easy to explain. Insert SQS when bursts, independent consumption,
backpressure, multiple consumers, or explicit replay become requirements.

## Security implications

Lambda invocation is restricted to each rule ARN; EventBridge DLQ writes are likewise
source-restricted. Application failures are visible as Lambda errors, not target DLQ
messages, because successful invocation delivery is distinct from function execution.

