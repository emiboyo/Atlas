# Milestone 6 Scope Proposal

> **Status: READY FOR GOVERNANCE REVIEW — NOT AUTHORISED**
>
> This document proposes scope only. It does not authorise implementation,
> production deployment, public access, external AI, live providers, financial
> advice, trading, execution, custody, payments, real money, or customer funds.

## Repository state

- Repository: `C:\Dev\Atlas`
- Proposal branch: `chore/milestone-6-governance-proposal`
- Baseline: `e83316636684887dcc24601584a4253192c33217`
- Milestone 5 final technical decision: conditional pass for governed private
  development in `docs/milestone-5-final-reaudit.md`.
- Authentication-entry UX correction: present in merge `e833166`.
- Milestone 6 implementation: absent.

The repository contains no roadmap document or accepted ADR that defines
Milestone 6. Every explicit Milestone 6 reference says it is prohibited or
requires separate approval. The homepage's non-authoritative roadmap names
“market context, portfolio insights, and explainable decision support” as the
next phase, while the README's approval-required next steps prioritise tracing,
SLOs, supply-chain assurance, provider governance, payments design, regulatory
boundaries, and resilience exercises. A scope choice is therefore required.

## Source references

| Source                                                                  | Relevant evidence                                                                                                          |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                                                             | Current platform boundary; approval-required operational, supply-chain, provider, payment, regulatory, and resilience work |
| `apps/web/src/app/page.tsx`                                             | Non-authoritative “Intelligence” and “Expansion” roadmap language                                                          |
| `docs/architecture.md`                                                  | Modular-monolith, PostgreSQL system-of-record, Redis ephemeral-state boundary                                              |
| `docs/release-readiness.md`                                             | Production blockers and required resilience/security evidence                                                              |
| `docs/milestone-5-governance.md` and ADR 0014                           | Existing research, AI, financial, tenancy, and stop boundaries                                                             |
| `docs/milestone-5-final-reaudit.md`                                     | Final Milestone 5 evidence and unresolved production prohibition                                                           |
| `docs/observability.md`                                                 | Current metrics/logging baseline and bounded-label rules                                                                   |
| `docs/security-risk-exceptions.md`                                      | Two unresolved, expiring development-only exceptions                                                                       |
| Research, backtest, data-quality, integrity, and threat-model documents | Determinism, provenance, append-only evidence, non-advisory language                                                       |
| Current routes, models, workflows, Compose, and manifests               | Implemented surface and operational controls                                                                               |

ADRs 0015–0017 already govern Milestone 5 engine/evidence/explanation design.
The Milestone 6 proposal is therefore uniquely numbered ADR 0018. No accepted
ADR was overwritten or renumbered.

## Current baseline through Milestone 5

### Implemented and tested

- Clerk session verification, local active-user and active-organisation checks,
  tenant membership, owner/admin/member/viewer roles, central server-derived
  permissions, foreign-resource concealment, and append-only identity audit.
- Provider-neutral market reference data, deterministic simulated development
  observations, tenant watchlists, provenance, freshness, and quality controls.
- Tenant-scoped simulated portfolios, immutable transactions and reversals,
  fixed-precision accounting, valuation snapshots, descriptive analytics, and
  portfolio audit evidence.
- Immutable research strategies and versions; deterministic historical
  simulation; events, equity points, results, comparisons, data-quality
  evidence, local deterministic explanations, and research audit records.
- Structured logs, request IDs, liveness/readiness, Prometheus metrics, Docker
  Compose web/API/PostgreSQL/Redis runtime, unit/integration/concurrency tests,
  and desktop/mobile Chromium accessibility automation.

### Technically accepted but restricted

Milestone 5 is conditionally passed for private development. This is not a
production-readiness decision. Production, public access, live providers,
external production AI, advice, personalised recommendations, real money,
orders, execution, brokerage, custody, payments, customer funds, and autonomous
financial action remain prohibited. Two security exceptions remain unresolved
and expire on 2026-10-27 unless separately reviewed.

### Future capability, not current capability

Production telemetry, approved SLOs, image signing, SBOM/attestation policy,
load/failover/restore evidence, live provider governance, payments, KYC/AML,
optimisation, recommendations, signals, automation, and live financial access
are future work. Their presence in architecture or roadmap text is not proof of
implementation or authorisation.

## Candidate scope discovery

| Candidate                                       | Evidence and purpose                                                                                                             | Dependencies and implied changes                                                                                  | Significance                                                         | Classification                         |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------- |
| Operational assurance and supply-chain evidence | README next steps and release-readiness gates; prove observability, resilience, recovery, and artifact provenance                | Test harnesses, runbooks, non-production telemetry design, CI evidence; no product data model required by default | Low financial/AI exposure; material security and operational benefit | Suitable                               |
| Research-to-portfolio decision support          | Homepage “portfolio insights” and existing portfolio/research foundations; compare historical research with simulated portfolios | New routes/APIs/entities, research/portfolio joins, permissions, provenance, quantitative review                  | Could be perceived as recommendation or portfolio management         | Split out/defer                        |
| Local AI research assistant                     | Mission/homepage intelligence language and existing deterministic explanations                                                   | Model/prompt boundary, storage, evaluation, injection controls, cost/privacy controls                             | High model, privacy, financial-promotion, and regulatory risk        | Defer                                  |
| Production market-data provider                 | README and provider ADR future boundary                                                                                          | Contracts, secrets, licensing, entitlements, quotas, reconciliation, outage handling                              | Live-data claims and commercial/regulatory exposure                  | Prohibited in M6                       |
| Stripe/payment activation                       | Existing configuration and payment architecture                                                                                  | Webhook worker, ledger/accounting rules, credentials, operational reconciliation                                  | Customer money and payment-services exposure                         | Prohibited in M6                       |
| KYC/AML/suitability                             | README future review item                                                                                                        | Restricted personal data, vendor and legal design, case management                                                | Major regulatory/privacy exposure                                    | Documentation-only; separate milestone |
| Trading, orders, automation, custody            | Mission and future domain model                                                                                                  | Brokers/exchanges, execution state machine, money movement, reconciliation                                        | Highest financial/regulatory impact                                  | Prohibited                             |

### Candidate impact dossiers

| Candidate                 | Data and users                                                                                   | Implied routes, APIs, and database                                                                  | External services                                                  | Boundary impact                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| Operational assurance     | Synthetic requests, build metadata, redacted telemetry, development backups; developers/auditors | Private assurance console; evidence-run API; optional evidence run/artifact/audit entities          | None required; local signing/telemetry preferred                   | Security/availability impact; no financial or AI function                                             |
| Research decision support | Historical candles, backtests, simulated portfolios; tenant researchers                          | Scenario/report UI and APIs; report/config/provenance entities and research-to-portfolio references | None required initially                                            | High quantitative and advice-perception risk; conflicts if it mutates portfolios or ranks investments |
| Local research assistant  | Persisted research evidence, prompts/outputs; tenant researchers/reviewers                       | Assistant UI/API; prompt/model/output/evaluation/audit entities                                     | Local model initially; any external provider separately prohibited | High AI/privacy/model risk; conflicts if output becomes recommendation or authority                   |
| Production market data    | Live/reference observations, entitlements; tenant users/operators                                | Provider administration/status APIs; ingestion, entitlement, reconciliation, licensing entities     | Data vendors/exchanges                                             | Conflicts with live-provider prohibition and creates licensing/freshness claims                       |
| Payments                  | Customer/payment/accounting data; finance operators/customers                                    | Billing/payment/webhook/reconciliation workflows; durable inbox and ledger relations                | Stripe/banks                                                       | Conflicts with payment, real-money, and customer-fund prohibitions                                    |
| KYC/AML/suitability       | Restricted identity, government, screening, and assessment data; compliance staff/customers      | Case/decision/evidence APIs and restricted entities                                                 | Identity/screening vendors                                         | Requires dedicated privacy and qualified regulatory design; documentation-only                        |
| Trading/orders/custody    | Orders, accounts, executions, balances, funds; customers/operators                               | Order/execution/custody APIs and state machines; extensive financial ledger entities                | Brokers, exchanges, banks, custodians                              | Directly prohibited and outside private historical-research authority                                 |

## Scope options

### Option A — Private Operational Assurance and Supply-Chain Evidence

Purpose: establish evidence that the existing Milestone 1–5 private runtime can
be observed, tested under bounded load and failure, restored, and traced to
reviewed build inputs without enabling production.

Features: OpenTelemetry and SLO design; private/local instrumentation where
approved; bounded synthetic load and fault exercises; backup/restore and
disaster-recovery evidence; SBOM, vulnerability, image-signing, provenance, and
attestation design/evidence; operational runbooks and dashboards using synthetic
or development data.

Risk/size/test burden: medium engineering size and high operational test burden,
but low financial and regulatory exposure. It depends on the existing Docker,
metrics, logging, CI, and AWS design but does not authorise deployment or cloud
resource creation.

Recommendation: **recommended only as the narrower Milestone 6A phase below**.
The in-application evidence surface and persistence layer remain deferred.

### Option B — Historical Research Decision-Support Workspace

Purpose: add non-advisory, tenant-scoped views that relate historical strategy
results to simulated portfolio context.

Features could include user-selected historical scenarios and descriptive
comparison reports. It would imply new APIs, database relations, audit records,
quantitative methods, and strong separation from portfolio mutation.

Risk/size/test burden: large; high quantitative and regulatory-language burden.
Ranking or personalisation could become advice. It should be separately scoped
after Option A evidence and qualified regulatory review.

Recommendation: defer and split into its own governance proposal.

### Option C — Bounded Local Research Assistant

Purpose: allow a local model to explain persisted historical evidence or draft
research templates without acting on them.

Risk/size/test burden: large; high prompt-injection, hallucination, privacy,
model-provenance, cost, and misleading-output burden. External AI and financial
actions would remain prohibited.

Recommendation: defer until a dedicated AI/model-risk decision and evaluation
framework exist.

## Recommended proposed scope

### Title

Milestone 6A — Local/CI Operational Evidence Foundation

### Objective and user problem

Provide maintainers and independent reviewers with repeatable evidence that the
existing private-development platform is observable, recoverable, resilient to
bounded synthetic failure, and traceable to reviewed software artifacts. This
addresses the current inability to make verified operational claims; it does
not deliver an investment feature.

### Supported users

- Atlas developers and authorised private testers.
- Security, reliability, data-integrity, and independent audit reviewers.
- No public customers or production operators.

### Permitted workflows

1. Generate an SBOM and provenance evidence for a commit-built web/API image.
2. Sign and verify development artifacts using non-production keys held outside
   source control, subject to an approved key-handling design.
3. Correlate allow-listed traces, metrics, and logs across a synthetic request
   without recording tokens, secrets, prompts, or financial/personal payloads.
4. execute bounded synthetic load, dependency-failure, restart, and recovery
   tests in isolated private environments.
5. Back up and restore synthetic/development PostgreSQL state, verify checksums
   and migrations, and record immutable exercise evidence.
6. Define and evaluate proposed service indicators and objectives; no document
   may label them production SLOs until separately approved.

### Inputs and outputs

Inputs are reviewed source commits, dependency lockfiles, container definitions,
synthetic requests/data, approved development fixtures, redacted operational
metadata, and disposable private databases. Outputs are SBOMs, attestations,
signing-verification records, bounded-cardinality telemetry, load/failure test
reports, backup/restore checksums, runbooks, and audit decisions.

### Architecture, data, AI, and financial boundaries

- Reuse Next.js, FastAPI, PostgreSQL, Redis, existing logs/metrics/request IDs,
  Docker Compose, CI, and runbooks.
- Any new evidence store must be append-only, tenant-neutral where possible,
  integrity-protected, retention-bounded, and unable to mutate domain records.
- Synthetic data only. Tenant historical data, personal data, portfolio data,
  research data, and financial data are prohibited in Milestone 6A. Any later
  use requires a new signed governance decision and is not covered by ADR 0018.
- No AI is required or permitted for the recommended scope.
- No portfolio, research, ledger, order, payment, custody, recommendation, or
  real-money state may be created or modified by Milestone 6 tooling.
- No Terraform apply, AWS deployment, Vercel production deployment, live
  provider, or production credential is permitted.
- Phase 6A creates no application console, application API, database entity,
  migration, cloud telemetry path, production signing infrastructure, or
  tenant-data resilience workflow.

### Dependencies on Milestone 5

The proposal relies on the accepted private-development baseline, stable health
and metrics endpoints, deterministic research fixtures, existing Docker
hardening, and audit evidence. It inherits every Milestone 5 restriction and
does not extend the two security exceptions unless the risk owner explicitly
does so in a signed decision.

### Explicit non-goals

Product analytics; strategy expansion; optimisation; signals; rankings;
personalised output; AI assistants; portfolio proposals or mutations; live
market data; production readiness; public access; deployment; trading; orders;
brokers; exchanges; banking; payments; wallets; custody; settlement; deposits;
withdrawals; advice; suitability; KYC/AML; real money; and customer funds.

## Proposed architecture and data flow

```text
Reviewed commit + lockfiles + container definitions
                    |
                    v
          private build/evidence runner
          |          |             |
          v          v             v
        SBOM     signed digest   test manifest
          \          |             /
           \         v            /
            -> append-only evidence bundle
                       |
Synthetic client -> web/API -> PostgreSQL/Redis
                       |
              allow-listed telemetry
                       |
     bounded load/fault/backup/restore verifier
                       |
             redacted audit report
```

Proposed components are an evidence orchestration boundary, telemetry policy,
fault/load harness, restore verifier, and evidence manifest. Exact technology,
storage schema, signature trust root, and retention remain design decisions.
PostgreSQL constraints must enforce any relational evidence integrity; process
validation alone is insufficient. Idempotency keys, unique evidence identities,
transactional commits, advisory/row locks where required, and fail-closed retry
semantics must be proven under separate sessions.

### Phase 6A architecture decisions

- Frontend/API/database: none. The assurance console,
  `/api/v1/operational-evidence`, persistent evidence models, migrations, and
  application permissions are deferred until an independent Phase 6A review
  proves they are necessary and a separate governance decision approves them.
- Evidence storage: retention-limited CI artifacts and integrity-protected local
  evidence bundles. No new operational-evidence database is permitted.
- Evidence integrity: each bundle contains a canonical manifest, source commit,
  tool versions, configuration digest, artifact digests, timestamps,
  environment classification, result, limitations, and SHA-256 checksums.
- Retention: CI artifacts and local bundles have a proposed maximum retention of
  30 days unless a named audit/legal hold is explicitly recorded. Review reports
  may retain referenced digests without retaining secrets or raw payloads.
- Signing: a development-only signing key is generated and held outside Git,
  container images, CI artifacts, logs, and evidence bundles. No production
  trust root, cloud KMS credential, or production signing identity is created.
  The corresponding public verification material and key identifier may be
  recorded. Revoke and replace the key on suspected exposure.
- Data: synthetic data only. Tenant historical data, personal data, portfolio
  data, research data, and financial data are prohibited in Milestone 6A. Any
  later use requires a new signed governance decision and is not covered by ADR 0018.
- Load limits: local/private allow-listed targets only; at most 10,000 requests,
  16 concurrent workers, and 15 minutes per exercise. The runner must also
  enforce configurable CPU, memory, connection, retry, and storage ceilings and
  stop on any ceiling, target mismatch, or health degradation.
- Proposed non-production indicators: request success/error counts, p50/p95/p99
  latency, saturation (CPU, memory, database connections), restart/recovery
  duration, backup/restore duration, and checksum/integrity result. These are
  development observations, not production SLOs or availability promises.
- Execution: reviewed local/CI commands and allow-listed configuration only. No
  browser input, arbitrary shell, arbitrary URL, cloud target, or external
  provider controls an exercise.

## Acceptance criteria

- Explicit signed governance approval selects Milestone 6A under ADR 0018
  before implementation.
- All implementation remains feature-flagged/private and uses synthetic data
  only; disabling it restores the Milestone 5 runtime path.
- No application-domain mutation, live integration, production deployment, or
  external AI path exists.
- Trace/log/metric schemas pass secret, PII, tenant-data, and cardinality review.
- SBOM, artifact digest, signature, provenance, and verification failure paths
  are reproducible and fail closed.
- Bounded load/fault/restart/backup/restore exercises have explicit limits,
  recovery-point/recovery-time observations, and data-integrity checks.
- Unit, integration, PostgreSQL, migration, constraint, tenancy, permission,
  idempotency, concurrency, fault, deterministic replay, API, frontend,
  accessibility, browser, dependency, Docker, and smoke gates pass as applicable.
- Python coverage is at least 80%; no unresolved Critical/High finding or
  material Medium integrity defect remains.
- An independent Milestone 6 audit accepts the evidence.

## Deferred work

Options B and C; production telemetry; production SLOs; cloud rollout; live
providers; customer data exercises; regulatory workflows; and every financial
capability are deferred.

## Unresolved approval prerequisites

1. Will the risk owner explicitly select Milestone 6A and approve the proposed
   30-day evidence retention and fixed load ceilings?
2. Will independent security/reliability reviewers accept the local/CI evidence
   bundle and development-key design?
3. Will both existing security exceptions be fixed or explicitly extended to
   this exact scope with current evidence?
4. Will the risk owner provide external evidence that both exposed Clerk
   development secret keys were revoked and only the rotated key remains active?

Until these questions are resolved through explicit governance approval,
Milestone 6 implementation may not begin.

## Financial and regulatory boundary analysis

This is an engineering risk analysis, not a legal conclusion. Qualified legal
or regulatory counsel must review any later scope that creates customer-facing
financial content or uses personal financial data.

| Interpretation                                                | Milestone 6A assessment and control                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Investment advice / personalised recommendation / suitability | Not required; prohibited. No ranking, target, recommendation, personalisation, or action output                              |
| Financial promotion                                           | Operational claims must not market returns, investment quality, certainty, or product availability; public use is prohibited |
| Portfolio management                                          | No portfolio or simulated-portfolio mutation, allocation, optimisation, or rebalance authority                               |
| Order execution / brokerage                                   | No order, broker, exchange, execution, or paper-to-live path                                                                 |
| Custody / payment service / intermediation                    | No money, wallet, account funding, settlement, deposit, withdrawal, or customer-fund path                                    |

All statements must distinguish development evidence from production readiness,
disclose assumptions and limitations, and avoid guarantees or certainty. If a
reviewer determines that a proposed workflow could fall within any listed
interpretation, implementation stops pending qualified review and a new signed
decision.
