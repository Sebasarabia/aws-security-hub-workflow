# Talk outline and speaker script (30 minutes)

SPDX-License-Identifier: MIT-0

Audience: builders, cloud engineers, security practitioners, and startup teams attending
Road to AWS Community Day Bolivia. Delivery language: Spanish, preserving official
service, schema, event, and API names in English.

## Session promise

Show a small, reproducible workflow that turns a Security Hub finding into a validated,
explainable, duplicate-safe decision without pretending that severity is organizational
risk or that automation should remediate resources automatically.

## Slide sequence

### 1. De hallazgo de seguridad a respuesta — 1 minute

- Subtitle: `Workflow event-driven con Terraform y Python`.
- State that this is a community educational reference, not an AWS-supported product.
- Show the repository URL: `github.com/Sebasarabia/aws-security-hub-workflow`.

Visual: a single horizontal signal-to-decision flow. Keep the title slide minimal.

### 2. Detectar no es responder — 2 minutes

Core line: a control can create a useful signal; response capability requires a trusted,
repeatable, observable workflow and an accountable human decision.

Avoid implying that centralizing alerts automatically creates incident response.

### 3. Signal, finding, exposure, incident — 2 minutes

- Signal: a technical observation.
- Finding: a structured observation with security context.
- Exposure: a condition that changes likelihood or potential impact.
- Incident: a confirmed event requiring coordinated response.

The four terms are related but are not an automatic maturity ladder.

### 4. Which AWS service contributes what — 2 minutes

- GuardDuty: threat and activity detections.
- Inspector: workload vulnerabilities and exposure.
- Macie: sensitive-data discovery in S3.
- AWS Config: configuration state and change history.
- Security Hub CSPM: posture controls and the ASFF compatibility path.
- Security Hub: the current OCSF-based signal and correlation path.

Do not imply that this repository enables any of these account-level services.

### 5. Security Hub is not Security Hub CSPM — 2 minutes

Use two separate lanes:

- Security Hub: OCSF 1.6, `Findings Imported V2`, one finding per event, preferred path.
- Security Hub CSPM: ASFF, `Security Hub Findings - Imported`, one finding per event,
  compatibility path.

Explain that `dual` is a migration/teaching mode and can surface logical duplicates.

Sources: AWS Security Hub introductions, OCSF guide, and EventBridge event-format pages
linked from `docs/research-notes.md`.

### 6. Minimum architecture — 2 minutes

```text
Security Hub / Security Hub CSPM
              ↓
         EventBridge ── failed target delivery ──> SQS DLQ
              ↓
        Python Lambda
         ├─> DynamoDB idempotency
         ├─> SNS escalation
         └─> CloudWatch logs, metrics, alarms
```

Explain why direct EventBridge-to-Lambda is appropriate for the bounded v1. Introduce
SQS before Lambda only for sustained bursts, backpressure, explicit replay, independent
consumption, or multiple consumers.

### 7. EventBridge routes; Lambda distrusts — 2 minutes

EventBridge performs only coarse source/detail-type filtering. Lambda revalidates:

- envelope fields and correlation ID;
- exactly one finding;
- expected schema family and required fields;
- bounded strings, timestamps, severity, state, and workflow status.

The declared source `aws.securityhub` is not treated as proof that payload fields are
safe to log or use.

### 8. Two adapters, one internal model — 2 minutes

```text
OCSF event → OCSF adapter ──┐
                            ├──> NormalizedFinding ──> common logic
ASFF event → ASFF adapter ──┘
```

Show `src/finding_processor/adapters/` and `models.py`. The business logic never reaches
back into OCSF- or ASFF-specific fields.

### 9. Explainable triage — 2 minutes

- `ESCALATE`: active HIGH or CRITICAL.
- `RECORD`: MEDIUM.
- `IGNORE`: LOW/INFORMATIONAL or resolved/suppressed.
- `REJECT`: invalid or unsupported input.
- `DUPLICATE`: repeated delivery of the same meaningful version.

Every result has a stable reason code. Severity is a teaching input, not a risk score.
Future context can include criticality, exposure, account purpose, data sensitivity,
exploitability, repetition, environment, ownership, and business impact.

### 10. Idempotency that understands updates — 2 minutes

Key material: schema family, finding ID, update timestamp fallback, and workflow-status
fallback. The exact duplicate cannot publish SNS twice. A meaningful update is processed
again. Powertools and DynamoDB provide concurrent in-progress protection and TTL.

Do not call the table an audit database.

### 11. Observability and failure semantics — 2 minutes

Distinguish visibly:

- EventBridge target-delivery failure → retry and SQS DLQ.
- Successful Lambda invocation followed by application error → Lambda error/log/alarm.
- Malformed finding → `REJECT`.
- Policy exclusion → `IGNORE`.
- Repeated delivery → `DUPLICATE`.

Logs are processing records, not forensic evidence. They contain correlation, decision,
reason code, masked account, and normalized product; never the raw event.

### 12. Live local demo — 6 minutes maximum

Follow `docs/demo-runbook.md` exactly:

```bash
make demo-local-ocsf
make demo-local-asff
```

Point out the synthetic label, masked account, sanitized notification, decision, reason
code, and schema family. Show the triage policy and one adapter. Use tests to explain
duplicate suppression rather than improvising a real AWS finding.

Honesty statement: this demonstrates application behavior without AWS credentials; it
does not prove EventBridge delivery or a live Security Hub integration.

### 13. Adoption path — 1 minute

1. Start in one account with clear notification ownership.
2. Tune thresholds, costs, retention, and operational response.
3. Add buffering/replay only when traffic requirements justify it.
4. Evolve toward a security account, regional aggregation, and multi-account routing.
5. Add business context before considering higher-impact automation.

### 14. Boundaries and cleanup — 1 minute

- No automatic isolation, credential revocation, IAM modification, or deletion.
- No vulnerable infrastructure or generated attacks.
- No production-readiness, compliance, or evidentiary-integrity claim.
- Terraform cleanup does not disable pre-existing account security services.

### 15. Automate the decision, not the damage — 1 minute

Closing line: validate aggressively, minimize data, suppress duplicates, notify humans,
and earn more automation through context and operational evidence.

Show the repository URL and invite the audience to run the local demo first.

## Demo contingency plan

If the terminal, dependency installation, or projector fails:

1. Show the expected sanitized OCSF output from `docs/demo-runbook.md` notes.
2. Walk through the fixture → adapter → normalized model → policy → notification path.
3. Show the green GitHub Actions/CodeQL result and the behavior test names.
4. Never replace the failed demo with an unreviewed AWS apply or attack simulation.

## Presenter checklist

- Fresh clone or clean working tree.
- Python 3.13 environment prepared before entering the room.
- `make check` and both demos executed on the presentation machine.
- Terminal font at least 22 pt; fixture and policy files pre-opened.
- Browser tab open at the tagged release or reviewed commit.
- Six-minute timer rehearsed twice.
- Backup terminal output and repository pages available offline.
- Cost, cleanup, synthetic-data, and no-remediation disclaimers stated aloud.

## Official source set

Use only the primary references already reconciled in `docs/research-notes.md`, especially
AWS Security Hub/OCSF, Security Hub CSPM, EventBridge retry/DLQ, Lambda best practices,
Powertools idempotency, HashiCorp Terraform, AWS Well-Architected Security Pillar, NIST
CSF 2.0 and SP 800-61r3, and the OWASP IaC/CI/CD/supply-chain guidance.
