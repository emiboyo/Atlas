# Security Risk Decisions and Recommendations

This register records approved, time-bounded security exceptions. Each exception applies only to
its stated scope and dates; none constitutes production authorisation.

## GHSA-mh99-v99m-4gvg / CVE-2026-14257

### Manual Risk Decision

**Decision:** APPROVED TEMPORARILY — DEVELOPMENT ONLY

**Risk owner:** Adebayo Olaegbe, Founder and Project Owner

**Security reviewer:** Independent security review required before production

**Approval date:** 2026-07-27

**Next review date:** 2026-08-27

**Expiry date:** 2026-10-27

Technical classification:

- Severity: high
- Component: `brace-expansion` 1.1.16
- Dependency path: `packages/eslint-config -> eslint -> minimatch -> brace-expansion`
- Classification: development and CI lint tooling; absent from the Atlas web runtime image
- Runtime reachability: no application route or production service invokes ESLint or accepts glob
  patterns for this dependency
- Exploitability: requires attacker-controlled brace patterns to reach the lint toolchain

**Approved scope:**

- Local development
- Automated testing
- Continuous integration linting
- Milestone 2 development work
- Bounded Milestone 4 private development as defined by
  [ADR 0009](adr/0009-milestone-4-private-development-authorisation.md)

**Prohibited scope:**

- Production deployment
- Public customer access
- Live trading
- Real-money investing
- Custody or movement of customer funds
- Any activity outside the authorised simulated-accounting and read-only-analytics boundary
- Processing untrusted user-controlled glob or brace patterns through the affected tooling

**Decision rationale:**

The affected package is introduced through the ESLint and minimatch development-tool chain. It is
not part of the Atlas web or API production runtime path. Attempts to force an incompatible
patched major version broke the existing linting chain, and the available ESLint upgrade path is
not currently compatible with the required React plugins. The exception is therefore accepted
temporarily for development use only, subject to these controls and review dates.

**Compensating controls:**

- ESLint is not included in the production runtime images.
- Untrusted customer input is not processed through the linting toolchain.
- Production deployment remains prohibited.
- Dependency auditing will continue.
- The exception must be reviewed when compatible ESLint and React-plugin versions become
  available.
- Untrusted arguments and pull-request-supplied workflow changes must not execute with elevated
  secrets.

**Immediate revocation conditions:**

- The affected package becomes reachable from application runtime code.
- Untrusted input is passed to the affected development tooling.
- A compatible patched version becomes available.
- The advisory severity or exploitability materially increases.
- Atlas begins public or production deployment.

**Approval status:** APPROVED TEMPORARILY

## CVE-2026-12087

### Manual Risk Decision

**Decision:** APPROVED TEMPORARILY — DEVELOPMENT ONLY

**Risk owner:** Adebayo Olaegbe, Founder and Project Owner

**Security reviewer:** Independent security review required before production

**Approval date:** 2026-07-27

**Next review date:** 2026-08-27

**Expiry date:** 2026-10-27

Technical classification:

- Severity: critical
- Component: Perl 5.40.1 in the official `python:3.12.13-slim` operating-system layer
- Classification: unused base-image component; Docker Scout reports no fixed Debian package
- Runtime reachability: Atlas starts Uvicorn directly and does not invoke Perl
- Exploitability: requires execution of the unused Perl interpreter; the API runs as a non-root
  user with a read-only root filesystem and `no-new-privileges`

**Approved scope:**

- Local development
- Milestone 2 development work
- Bounded Milestone 4 private development as defined by
  [ADR 0009](adr/0009-milestone-4-private-development-authorisation.md)
- Internal Docker Compose testing

**Prohibited scope:**

- Production deployment
- Public customer access
- Live trading
- Real-money investing
- Real deposits, withdrawals, payments, brokerage, execution, or customer-fund handling
- Any activity outside the authorised simulated-accounting and read-only-analytics boundary
- Executing Perl inside the API container
- Adding application dependencies or scripts that invoke Perl

**Decision rationale:**

Docker Scout identified CVE-2026-12087 in a Perl component inherited from the official Python
3.12.13 slim base image. Atlas starts Uvicorn directly and does not invoke Perl. At the time of
validation, no fixed Debian package was reported for the selected base image.

The exception is accepted temporarily for private development only. It does not approve
production use of the affected image.

**Compensating controls:**

- Atlas does not invoke Perl.
- The API runs as a non-root user.
- The API root filesystem is read-only.
- `no-new-privileges` is enabled.
- The container has no host bind mounts.
- The application is not publicly deployed.
- Docker image scans will be repeated when the base image is updated.

**Immediate revocation conditions:**

- Atlas begins invoking Perl directly or indirectly.
- The affected component becomes reachable from external input.
- A fixed official Python base image becomes available.
- The advisory severity or exploitability materially increases.
- Atlas is prepared for public or production deployment.

**Approval status:** APPROVED TEMPORARILY

## Milestone 4 scope-extension control

The bounded scope extension recorded in
[ADR 0009](adr/0009-milestone-4-private-development-authorisation.md) applies to both existing
exceptions. It does not change their risk owner, review date, expiry date, compensating controls,
revocation conditions, unresolved status, or production prohibition. It creates no new
vulnerability exception and grants no authority for public access, real money, customer funds,
live providers, trading, or Milestone 5.

## Milestone 5 scope-extension control

The new dated decision in
[ADR 0014](adr/0014-milestone-5-private-development-authorisation.md) extends both existing
development-only exceptions solely to bounded Milestone 5 explainable strategy research,
historical backtesting, and simulation.

Both vulnerabilities remain unresolved. Risk owner Adebayo Olaegbe, review date 2026-08-27,
expiry date 2026-10-27, compensating controls, immediate revocation conditions, and production
prohibitions are unchanged. The extension authorises no public access, live provider, production
AI credential, real money, broker, order, execution, custody, advice, autonomous financial
action, customer funds, or Milestone 6. Scope expires automatically without a new recorded
decision.
