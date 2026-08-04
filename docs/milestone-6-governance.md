# Milestone 6 Governance Proposal

> **Status: PROPOSED — NOT YET AUTHORISED**

## Governance identity

- Proposed scope: Milestone 6A — Local/CI Operational Evidence Foundation
- Risk owner: Adebayo Olaegbe (proposed; signature required)
- Reviewer: Independent security, reliability, data-integrity, and governance
  review required
- Proposal date: 2026-08-03
- Proposed review date: 2026-08-17
- Proposed expiry: 2026-10-27
- Baseline: `e83316636684887dcc24601584a4253192c33217`

The dates above are proposals, not inherited authority. The proposed expiry is
no later than the existing development-risk exceptions. Those exceptions do
not cover Milestone 6 unless explicitly extended by the risk owner.

## Proposed permitted activity

Only after a signed approval selects Milestone 6A:

| Capability                                                                        | Proposed classification | Conditions                                                           |
| --------------------------------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------- |
| Architecture, threat, test, rollback, and runbook design                          | Private development     | Documentation and review first                                       |
| SBOM, artifact digest, development signing, provenance, and verification evidence | Private development     | Non-production keys; secrets outside source; fail closed             |
| Bounded tracing/metrics/logging changes                                           | Private development     | Allow-listed fields, bounded labels, no payload/token/secret capture |
| Synthetic load, fault, restart, and recovery exercises                            | Synthetic data only     | Isolated limits, kill switch, no external targets                    |
| PostgreSQL backup/restore and migration exercises                                 | Synthetic data only     | Disposable environment, checksums, no silent repair                  |
| Evidence manifests and independent audit reports                                  | Private development     | Append-only/integrity-protected and retention-bounded                |
| Feature flags and deterministic fallback                                          | Private development     | Disabled state preserves Milestone 5 behaviour                       |

Phase 6A does not permit an assurance console, application API, database model
or migration, cloud telemetry, production signing infrastructure, or tenant-data
resilience exercise.

## Prohibited activity

- Production deployment, public access, production credentials, Terraform
  apply, or treating Compose evidence as production readiness.
- Live market-data, AI, broker, exchange, payment, bank, wallet, custody,
  settlement, order-routing, execution, or customer-fund integration.
- Deposits, withdrawals, real money, live or paper-to-live transactions.
- Investment advice, personalised recommendations, suitability assessment,
  expected-return promises, guarantees, rankings presented as advice, signals,
  target allocations, optimisation, or autonomous financial decisions.
- Any AI-triggered or AI-controlled portfolio or simulated-portfolio transaction,
  with or without user confirmation.
- Production external AI, model training on tenant/customer data, prompt or
  output paths, or AI-generated operational authority.
- Capturing Clerk tokens, secrets, request bodies, personal data, strategy
  source, portfolio values, or unbounded identifiers in telemetry.
- Extending Option A into Options B or C without a new signed decision.
- Milestone 7 or later work.

## Implementation conditions

Implementation remains prohibited until all conditions are satisfied:

1. Closure evidence and separate proposed exception decisions are prepared
   without accepting risk.
2. Independent reviewers assess the scope, threat model, risk register, data
   classification, telemetry schema, rollback design, test plan, proposed
   exceptions, and Clerk attestation limitation.
3. The risk owner then records decisions, signs any accepted exceptions,
   acknowledges the independent review of the signed Clerk attestation and its
   provider-verification limitation, explicitly selects the scope, and signs the
   authorisation ADR.
4. Implementation begins only after final approval and every condition is met.
5. ADR 0018 remains the unique proposal record without rewriting accepted
   history.
6. Existing security exceptions are fixed or explicitly extended to this exact
   scope with current evidence and dates.
7. Exact artifact-signing key ownership and non-production secret handling are
   approved.
8. Work is decomposed into reviewable changes; application behaviour remains
   disabled by default until its focused evidence passes.
9. No legal/regulatory reviewer identifies a need for review that has not been
   completed.

## Authentication, authorisation, and tenancy

- Clerk authenticates; Atlas local state authorises. Active user, active
  organisation, current membership, and central permissions are mandatory.
- Owner/admin/member/viewer permissions must be explicitly mapped for every new
  endpoint. UI visibility never grants authority.
- Client-claimed tenant, role, permission, evidence status, artifact identity,
  provenance, or audit attribution is rejected.
- Foreign IDs and direct-object references conceal existence consistently.
- Membership deletion, suspension, ownership change, or session revocation must
  fail closed on the next server-authorised operation.
- Service-to-service work requires a separately designed, least-privilege
  workload identity. User credentials must not be repurposed.
- Audit events attribute verified actor/workload, tenant where applicable,
  request ID, operation, immutable input/output digest, and result.

## Data governance

| Class                           | Rule                                                                                           |
| ------------------------------- | ---------------------------------------------------------------------------------------------- |
| Synthetic fixtures              | Default for all tests and resilience exercises                                                 |
| Historical market/research data | Prohibited in Milestone 6A; requires a new signed governance decision                          |
| Personal/tenant financial data  | Prohibited in Milestone 6A; requires a new signed governance decision                          |
| Secrets/tokens/signing keys     | Never logged, persisted in evidence, committed, or exposed to clients                          |
| Audit/evidence data             | Append-only, integrity-protected, attributable, retention-bounded                              |
| Derived telemetry               | Allow-listed, bounded-cardinality, labelled with source/version/time                           |
| Backup data                     | Encrypted where supported, access-controlled, checksum-verified, deleted by approved retention |

No historical evidence may be silently repaired, deleted, or rewritten. A
correction must append a linked correction record. Material outputs require
source commit, image digest, tool/version, configuration digest, timestamps,
environment classification, and completeness/limitations.

## Phase 6A architecture decisions

- Evidence storage: integrity-protected local bundles and CI artifacts only; no
  operational-evidence database. Maximum proposed retention is 30 days unless
  an explicit audit/legal hold is recorded.
- Data: synthetic data only. Tenant historical data, personal data, portfolio
  data, research data, and financial data are prohibited in Milestone 6A. Any
  later use requires a new signed governance decision and is not covered by ADR 0018.
- Signing: a development-only key outside Git, images, logs, and artifacts; no
  production trust root or cloud KMS credential. Public verification material
  may be retained with a key identifier.
- Load: allow-listed local/private targets; maximum 10,000 requests, 16
  concurrent workers, and 15 minutes, plus CPU, memory, connection, retry, and
  storage ceilings with automatic stop.
- Indicators: development-only success/error count, p50/p95/p99 latency,
  saturation, recovery duration, restore duration, and checksum result. They
  are not production SLOs or availability promises.

## Existing security-exception decision required

No existing decision authorises Milestone 6A. Five separate current proposals
are documented in `docs/milestone-6a-security-exception-proposals.md`; all are
**PROPOSED — NOT ACCEPTED**:

| Proposal   | Advisory                             | Current path/status                                                                                           |
| ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| M6A-EX-001 | GHSA-mh99-v99m-4gvg / CVE-2026-14257 | `brace-expansion` 1.1.16 through ESLint/minimatch development tooling; no application-runtime path identified |
| M6A-EX-002 | CVE-2026-13221                       | Perl 5.40.1-6 inherited from the Python slim base; present in authenticated remediated-image scan             |
| M6A-EX-003 | CVE-2026-12087                       | Perl 5.40.1-6 inherited from the Python slim base; present in authenticated targeted and Critical/High scans  |
| M6A-EX-004 | CVE-2026-48959                       | Perl 5.40.1-6 inherited from the Python slim base; present in authenticated remediated-image scan             |
| M6A-EX-005 | CVE-2026-48962                       | Perl 5.40.1-6 inherited from the Python slim base; present in authenticated remediated-image scan             |

The remediated API image digest is
`99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`.
It is healthy and contains no runtime `pip`; 139 Python tests passed with
86.01% coverage, and `pip-audit` reported no vulnerable pinned Python package.
Scout still reports 2 Critical and 2 High findings in inherited Perl. These
checks support review but do not resolve a finding or accept an exception.

## Clerk secret-incident closure gate

Local verification on 2026-08-03 established:

- `apps/web/.env.local` and root `.env` are ignored and untracked;
- no Clerk secret pattern was found in tracked files or scanned Git history;
- the configured current development secret was not present in inspected web
  image metadata or current web logs; and
- a current secret is configured without recording its value.

The risk owner states that both exposed Clerk Development secret keys were
deleted and only one rotated Development secret remains active. The signed
factual risk-owner attestation at
`docs/evidence/milestone-6a/clerk-key-revocation-attestation.md` records the
signed factual testimony without values, complete identifiers, publishable
keys, or a retained screenshot. Provider state was not independently inspected.
M6-R006 remains open with the risk-owner attestation provided and independent
limitation review required; this does not prevent the completed evidence
package from entering independent review.

## Evidence and test requirements

- Formatting, lint, strict typecheck, package/Python tests, and production build.
- Python coverage at least 80%; coverage may not be reduced to pass.
- Real-PostgreSQL migration upgrade, downgrade where safe, re-upgrade, fresh
  install, drift check, direct constraints, RESTRICT/deferred constraints, and
  malformed-data preflight evidence.
- Tenant isolation, permissions, IDOR, client-claim rejection, revoked identity,
  idempotency, replay, duplicate, independent-session concurrency, rollback,
  and fault-injection tests.
- Deterministic replay, evidence digest, signature verification, tamper negative
  controls, stale/malformed/missing data, and recovery integrity tests.
- OpenAPI/schema, frontend workflow, WCAG 2.2 AA, keyboard, desktop/mobile browser,
  dependency audit, container scan, Docker health, runtime smoke, and manual
  user-journey evidence.
- No unremediated Critical or High finding may remain unless it is covered by a
  separate, explicitly accepted, signed, time-bounded exception with verified
  compensating controls, monitoring, review, expiry, and immediate revocation
  conditions. No material Medium integrity defect may remain unresolved.
- Full exact commands, failures, corrections, totals, and reruns recorded.
- Independent Milestone 6 audit before technical acceptance.

## Failure handling and rollback

Instrumentation and evidence generation must fail without mutating portfolio,
research, ledger, identity, or market records. Evidence writes are atomic and
idempotent; partial bundles are rejected. Provider/tool/signing/telemetry outage
must degrade to an explicit unavailable state, never fabricated success.
Rollback disables the feature flag, stops the isolated runner, revokes
development signing material, restores the last verified database backup only
through an approved exercise, and preserves failure/audit evidence.

## Stop conditions

Stop immediately if scope expands; live financial capability, public access,
real credentials/funds, or deployment is introduced; tenant crossover becomes
possible; database/evidence integrity cannot be enforced; deterministic
evidence is lost; external AI becomes necessary; required legal review is
absent; a new or materially changed Critical/High finding appears without an
explicitly accepted, signed, in-date exception, or a material Medium integrity
defect appears; Python coverage drops below 80%; an exception expires;
secret/PII leakage is detected; or a production/Terraform action is attempted.

## Audit and production boundary

The proposal may be independently reviewed, but passing implementation tests
would authorise only bounded private development. Production/public readiness
requires a separate decision, fresh security and regulatory review, resolved
exceptions, live-environment architecture, operational ownership, and explicit
approval. No wording in these documents weakens that boundary.

## Milestone 7 boundary

Milestone 7 is undefined and prohibited. Milestone 6 completion would not
authorise it.

## Decision framework

| Decision                         | Exact meaning                                                                                                                                           |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| APPROVED FOR PRIVATE DEVELOPMENT | Signed selection of Milestone 6A; all preconditions met; only listed private activities permitted until expiry                                          |
| APPROVED WITH CONDITIONS         | Signed selection of Milestone 6A with named conditions, owners, due dates, compensating controls, and stop triggers; unmet preconditions remain blocked |
| DEFERRED                         | No implementation; resolve ambiguity, dependencies, exceptions, legal review, or evidence design and resubmit                                           |
| REJECTED                         | No implementation; proposed risk or boundary is unacceptable and requires a materially new proposal                                                     |

This proposal makes none of those final decisions. **Milestone 6 is not
authorised until the risk owner explicitly signs an accepted decision.**
