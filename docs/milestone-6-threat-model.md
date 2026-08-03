# Milestone 6 Threat Model Proposal

> **Status: PROPOSED — NOT IMPLEMENTATION AUTHORITY**

## System boundary

Milestone 6A is a local/CI operational-evidence boundary around the existing
Docker and CI development stack. It may generate local telemetry policy
evidence, SBOM/provenance/signature records, bounded synthetic load/fault
evidence, and backup/restore verification. It creates no application console,
API, database entity, migration, cloud telemetry path, or tenant-data workflow.
It cannot make financial decisions or mutate Atlas domain state.

Identity, role, and tenancy threats apply only when Phase 6A exercises the
existing Atlas application using synthetic users and data. Phase 6A introduces
no new user-facing authorisation surface, tenant entity, or application
permission.

## Assets

Source commits and lockfiles; image/artifact digests; development signing keys;
SBOMs and attestations; telemetry; evidence manifests; audit records; synthetic
fixtures; backups; tenant identifiers; user/workload identity; configuration;
availability; and the integrity of Milestone 1–5 records.

## Actors

Authorised developer, authorised private tester, independent auditor,
authenticated tenant user, compromised account, malicious insider, external
attacker, compromised dependency/tool/provider, and faulty automation.

## Trust boundaries and data flows

```text
developer/auditor -> reviewed local/CI authority -> evidence runner
CI/build inputs -> build boundary -> artifact/SBOM/signature evidence
synthetic client -> web/API -> PostgreSQL/Redis
web/API -> allow-listed telemetry boundary -> private evidence sink
PostgreSQL backup -> isolated restore verifier -> checksum/audit result
```

Trust changes at identity verification, tenant authorisation, build runners,
container boundaries, database/Redis connections, telemetry export, signing
operations, backup storage, and auditor access.

## Threat analysis

| Threat                            | Asset                        | Actor / attack path                                        | Likelihood | Impact   | Mitigation                                                                                        | Verification evidence                              | Residual risk                   | Owner                   |
| --------------------------------- | ---------------------------- | ---------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------- | ----------------------- |
| Spoofed user/workload             | Evidence authority           | Forged session or workload identity                        | Medium     | High     | Clerk verification, local active state, audience/issuer checks, least-privilege workload identity | Invalid/revoked/expired token tests                | Provider/config compromise      | Identity owner          |
| Tampered artifact or SBOM         | Supply-chain evidence        | Replace image, manifest, digest, or signature              | Medium     | High     | Content digests, signatures, immutable provenance, trusted verification root                      | Positive and tamper negative controls              | Signing-key compromise          | Security owner          |
| Repudiation                       | Audit evidence               | Actor denies exercise or approval                          | Medium     | High     | Append-only attributed audit, request/evidence IDs, timestamps and digests                        | Audit completeness and immutability tests          | Privileged database compromise  | Governance owner        |
| Information disclosure            | Secrets/PII/tenant data      | Telemetry, logs, bundles, backups expose values            | Medium     | High     | Allow-list schemas, redaction, no bodies/tokens, encryption/access control                        | Secret/PII canary scans and access tests           | Novel fields or operator error  | Data owner              |
| Denial of service                 | Private stack                | Unbounded traces, labels, load, retries, or storage        | Medium     | High     | Hard quotas, bounded cardinality/load, timeouts, backpressure, kill switch                        | Saturation and limit tests                         | Shared-host contention          | Reliability owner       |
| Elevation of privilege            | Evidence/admin operations    | UI claim or weak endpoint permission                       | Medium     | High     | Central server permissions; deny by default; no client authority                                  | Role matrix and forged-claim tests                 | Permission-design defect        | Security owner          |
| Tenant crossover                  | Tenant/evidence data         | Guessed ID, missing composite key, shared trace            | Medium     | Critical | Tenant-scoped queries/constraints, foreign concealment, tenant-safe correlation IDs               | Cross-tenant API and direct PostgreSQL tests       | Misconfigured exporter          | Data owner              |
| Role manipulation                 | Authorisation                | Client supplies owner/admin or stale membership            | Medium     | High     | Server-loaded current membership; reject claims; fail on removal/suspension                       | Per-role and concurrent revocation tests           | Clerk/local sync delay          | Identity owner          |
| Replay/duplicate operation        | Evidence integrity           | Repeat signing, restore, or evidence request               | High       | Medium   | Scoped idempotency key plus payload fingerprint and unique constraints                            | Identical/conflicting concurrent retry tests       | External tool side effects      | Platform owner          |
| Race condition                    | Evidence/backup state        | Concurrent generate/archive/restore/rotate                 | Medium     | High     | Transactions, locks, uniqueness, state machine, atomic publication                                | Separate-session concurrency and commit-time tests | Database outage timing          | Data owner              |
| Stale or malformed data           | Operational conclusion       | Reuse old image/config/result or malformed telemetry       | High       | High     | Freshness, schema/version, provenance, completeness, reject unknown fields                        | Stale/malformed/missing input tests                | Clock/config error              | Reliability owner       |
| External tool/provider compromise | Build/evidence               | Scanner, registry, action, exporter compromised            | Medium     | Critical | Pin/review tools, least privilege, offline verification, egress limits, provenance                | Dependency/action review and compromise drill      | Upstream zero-day               | Security owner          |
| Secret leakage                    | Credentials/signing key      | Logs, process args, CI artifact, browser bundle            | Medium     | Critical | Secret store, masked channels, server-only variables, key rotation/revocation                     | Repository/image/log scans and rotation drill      | Insider access                  | Security owner          |
| Evidence poisoning                | Audit decision               | Crafted fixture or falsified result makes pass             | Medium     | High     | Reviewed fixtures, signed manifest, independent rerun, negative controls                          | Reproducibility and known-bad controls             | Colluding reviewers             | Audit owner             |
| Backup poisoning or rollback      | Recovery integrity           | Restore wrong/older/mutated backup                         | Medium     | Critical | Encrypted versioned backups, manifest/checksum, monotonic migration checks                        | Wrong-backup and corrupted-backup rejection        | Key compromise                  | Data owner              |
| Silent repair/deletion            | Historical evidence          | Migration or cleanup rewrites failing evidence             | Low        | Critical | Pre-DDL validation, append-only corrections, RESTRICT, retention approval                         | Malformed-upgrade and deletion tests               | DBA superuser                   | Data owner              |
| Prompt injection                  | Operational authority        | AI interprets malicious evidence                           | Low        | High     | AI is absent/prohibited; no model or prompt path                                                  | Architecture and dependency inspection             | Future scope drift              | AI-risk owner           |
| Model hallucination               | Operational/financial output | AI fabricates pass, cause, or recommendation               | Low        | High     | AI absent; deterministic tools and human review                                                   | No-model-path inspection                           | Future scope drift              | AI-risk owner           |
| Data poisoning                    | Metrics/research evidence    | Malicious observations influence conclusions               | Medium     | High     | Synthetic reviewed fixtures, provenance, quality gates, isolation                                 | Poisoned-fixture negative tests                    | Subtle statistical manipulation | Quant/data owner        |
| Misleading financial output       | Users/reputation             | Operational evidence presented as return/advice            | Low        | High     | No financial output; safe labels; non-advisory disclaimer                                         | Copy/API schema review                             | User inference                  | Product-risk owner      |
| Unauthorised financial action     | Portfolio/ledger             | Tool invokes domain mutation or execution path             | Low        | Critical | Network/API deny-list, read-only domain credentials where feasible, no such workflow              | Mutation canary and route/dependency inspection    | Privileged insider              | Financial-systems owner |
| Regulatory misrepresentation      | Public/governance claims     | “Production ready”, guarantee, advice, or compliance claim | Medium     | High     | Qualified review, controlled wording, explicit private status                                     | Documentation and UI copy review                   | Jurisdictional ambiguity        | Governance/legal owner  |
| Cross-environment action          | Production systems           | Private runner receives production target/credential       | Low        | Critical | Environment allow-list, no production credentials, fail-closed target validation                  | Production-host negative controls                  | Mislabelled environment         | Platform owner          |
| Unsafe deletion/retention         | Evidence/backups             | Broad cleanup removes required records                     | Medium     | High     | Explicit IDs, retention holds, recoverable deletion, dual review                                  | Scope and restore tests                            | Operator error                  | Data owner              |

Likelihood and impact are provisional and require independent review.

## Mitigation principles

Authentication is not authorisation; UI state is never authority. Domain data
is read-only to Milestone 6 tooling. PostgreSQL constraints enforce relational
integrity. Evidence creation is atomic, idempotent, attributable, and append-only.
Telemetry is allow-listed and bounded. Outages and unverifiable artifacts return
explicit failure/unavailable states. Synthetic fixtures are the default.

## Verification

Verification requires real-PostgreSQL constraint and concurrency evidence,
identity/tenant/permission matrices, signature/tamper negative controls,
secret/PII canaries, bounded-load and failure tests, corrupt/stale backup
rejection, deterministic reruns, Docker runtime checks, and independent audit.

## Assumptions

The work remains private; production credentials and targets are absent;
Milestone 6A is the only candidate considered; existing Milestone 5 controls
remain effective; and reviewers have access to exact commands and immutable
local/CI evidence.

## Exclusions

This model does not approve or fully model live providers, external AI, advice,
trading, orders, brokerage, exchange, banking, payments, wallets, custody,
settlement, real money, public users, production deployment, or Milestone 7.
Any such scope requires a new threat model and signed decision.
