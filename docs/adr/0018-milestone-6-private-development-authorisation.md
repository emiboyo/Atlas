# ADR 0018 — Milestone 6 Private-Development Authorisation Proposal

## Status

**PROPOSED — NOT YET AUTHORISED**

> **NOT AUTHORISED UNTIL EXPLICITLY APPROVED**

## Context

Milestone 5 is conditionally accepted for governed private development. It does
not authorise Milestone 6, production, public access, live providers, external
production AI, advice, trading, execution, payments, custody, or real money.

The repository does not define one authoritative Milestone 6. It presents
operational-assurance work, historical decision-support language, and future AI
possibilities. The scope proposal compares these options and recommends the
lowest-risk, directly evidenced option: private operational assurance and
supply-chain evidence.

ADRs numbered 0015, 0016, and 0017 already govern Milestone 5 decisions. This
proposal therefore uses the next unique number, ADR 0018, without rewriting or
renumbering accepted history.

## Proposed decision

Approve with conditions only the initial part of Option A from
`docs/milestone-6-scope-proposal.md`: **Milestone 6A — Local/CI Operational
Evidence Foundation**. The assurance console, application API/database,
cloud/production capability, Options B and C remain deferred. This text is a
proposal and makes no final decision.

## Proposed scope

- Development-only SBOM, artifact digest, provenance, signing-verification, and
  attestation evidence using non-production trust material.
- Allow-listed, bounded-cardinality tracing/metrics/logging for private tests.
- Bounded synthetic load, dependency-failure, restart, and recovery exercises.
- Synthetic/development PostgreSQL backup, restore, checksum, migration, and
  disaster-recovery evidence.
- Runbooks, proposed non-production service indicators/objectives, evidence
  manifests, and independent audit records.

Phase 6A stores evidence only as retention-limited CI artifacts and
integrity-protected local bundles. It uses synthetic data only, fixed local
load ceilings, and a development-only signing key held outside Git, images, and
evidence bundles. It creates no application route, API, database entity, cloud
telemetry path, production trust root, or cloud KMS credential.

## Proposed permitted actions

After explicit approval only: design and implement the exact Phase 6A private
scope; create synthetic fixtures; operate isolated Docker/private CI test
environments; generate and verify development artifacts and local/CI evidence;
add narrowly required harnesses, scripts, CI validation, and documentation after
design review; and perform independent audit. Application routes, APIs,
migrations, and database models are not permitted in Phase 6A.

## Prohibited actions

Production/public deployment; Terraform apply; production credentials or keys;
live providers; external AI; brokers; exchanges; orders; routing; execution;
banking; payments; wallets; custody; settlement; deposits; withdrawals; real
money; customer funds; investment advice; personalised recommendations;
suitability; ranking as advice; promises/guarantees; portfolio optimisation or
mutation; autonomous financial decisions; Options B/C; and Milestone 7.

Any autonomous, AI-triggered, or AI-controlled portfolio transaction or
simulated-portfolio transaction is prohibited, with or without user
confirmation. Only the deterministic Milestone 5 backtest engine may generate
historical simulated events from an explicitly user-approved immutable backtest
configuration; AI output cannot create or modify those events.

## Constraints

- Clerk authenticates and Atlas server-side local state authorises.
- Active user, active organisation, membership, central role permission,
  foreign-resource concealment, and current revocation checks are mandatory.
- Synthetic data only. Tenant historical data, personal data, portfolio data,
  research data, and financial data are prohibited in Milestone 6A. Any later
  use requires a new signed governance decision and is not covered by ADR 0018.
  Secrets, tokens, and unbounded labels must not enter evidence or telemetry.
- Domain data is read-only to Milestone 6 tooling. Evidence is atomic,
  idempotent, attributable, integrity-protected, append-only, and retention-bound.
- Feature disablement must preserve Milestone 5 behaviour.
- Existing security exceptions require a new explicit scope decision and may
  not be inferred to cover this milestone.
- Qualified legal/regulatory review is required if any output could be viewed
  as financial promotion, advice, recommendation, suitability, portfolio
  management, execution, brokerage, custody, payment service, or intermediation.

## Alternatives

1. Historical research decision-support workspace: deferred because it creates
   quantitative, personalisation, advice-perception, and portfolio-boundary risk.
2. Bounded local research assistant: deferred pending dedicated AI governance,
   privacy design, evaluation, and human-review controls.
3. Reject or defer all Milestone 6 work: appropriate if scope, ADR numbering,
   exceptions, key custody, or evidence architecture cannot be resolved.

## Consequences

If later approved, Atlas may improve evidence about the private-development
platform without adding an investment capability. Engineering and independent
audit cost will increase. Passing Milestone 6 will still not establish
production readiness or authorise later milestones. Failure or ambiguity leaves
the Milestone 5 boundary unchanged.

## Evidence gates

- Full lint, format, strict typing, unit, integration, security, production
  build, dependency, container, Docker health, and runtime smoke evidence.
- Real PostgreSQL migration, constraint, tenancy, permission, idempotency,
  concurrency, fault, rollback, replay, and recovery evidence.
- SBOM/provenance/signature positive and tamper-negative evidence.
- Telemetry secret/PII/cardinality review and bounded-load negative controls.
- Python coverage at least 80%; no unresolved Critical/High finding or material
  Medium integrity defect.
- Desktop/mobile accessibility and manual private user journey where UI changes.
- Exact commands, totals, failures, corrections, and reruns.
- Focused independent Milestone 6 audit.

## Security-exception and secret-incident gates

GHSA-mh99-v99m-4gvg / CVE-2026-14257 remains reported through the
ESLint/minimatch/`brace-expansion` development chain. An authenticated scan of
remediated API image digest
`62cf21a8719ebb8915b9a4943c613e05bd78f2293dc36cceb5af82418130e6c9`
reports CVE-2026-13221, CVE-2026-12087, CVE-2026-48959, and CVE-2026-48962
in inherited Perl 5.40.1-6. The existing decisions do not authorise Milestone
6A. Five separate decisions in
`docs/milestone-6a-security-exception-proposals.md` are **PROPOSED — NOT
ACCEPTED** pending independent review and explicit risk-owner decisions,
signatures, review dates, and expiry dates.

The risk owner states that both exposed Clerk Development secret keys were
deleted, only one rotated Development secret remains active, and Atlas
authenticated after rotation. The signed factual attestation records that
testimony without secret values, complete identifiers, publishable keys, or a
retained screenshot. The risk owner signed that factual attestation on
2026-08-03. This does not accept any exception or approve this ADR. Provider
state was not independently inspected, and an independent reviewer must assess
that limitation before authorisation.

The required sequence is: complete evidence and unsigned proposed exceptions;
independent review; risk-owner decisions and signatures; then separate final
approval of this ADR. Implementation may begin only after that final approval.
Readiness for independent review is not implementation authority.

## Expiry and review

- Proposal date: 2026-08-03
- Proposed review date: 2026-08-17
- Proposed expiry: 2026-10-27

These dates are not approved. Any final authority expires automatically on its
approved date and immediately on a stop condition. A final date may not silently
extend an existing exception.

## Approval

**NOT AUTHORISED UNTIL EXPLICITLY APPROVED**

- Final decision: _Unsigned_
- Risk owner: Adebayo Olaegbe
- Risk-owner signature: _Required_
- Decision date: _Required_
- Approved scope option: _Required_
- Conditions and owners: _Required_
- Independent reviewers: _Required_
- Review date: _Required_
- Expiry date: _Required_

Until every required field and external closure gate is completed, Milestone 6
implementation may not begin.
