# ADR 0006: Milestone 1 Security Risk Decision

- **Status:** Approved temporarily for private development
- **Risk owner:** Adebayo Olaegbe, Founder and Project Owner
- **Decision date:** 2026-07-27
- **Next review date:** 2026-08-27
- **Expiry date:** 2026-10-27
- **Scope:** Local development, automated testing, CI linting, internal Docker Compose testing,
  and Milestone 2 private development
- **Production approval:** Not granted
- **Independent security review:** Required before production

## Context

Atlas AI completed its Milestone 1 technical foundation audit with a conditional pass. Functional,
testing, database, Docker, Redis, migration, health-check, and infrastructure validation gates
passed.

Two security advisories remain unresolved because compatible fixes were not available at the time
of validation without breaking supported tooling or replacing an affected upstream base-image
component:

1. GHSA-mh99-v99m-4gvg / CVE-2026-14257 in the ESLint/minimatch development-tool chain.
2. CVE-2026-12087 in an unused Perl component inherited from the official Python API base image.

The detailed reachability analysis, controls, prohibited uses, and revocation conditions are
maintained in [`docs/security-risk-exceptions.md`](../security-risk-exceptions.md).

## Decision

Both findings are approved temporarily for private development within their documented controls
until 2026-10-27, subject to review on 2026-08-27.

Permitted:

- Local and private development
- Automated testing
- Continuous integration linting
- Internal Docker Compose testing
- Milestone 2 private development

Prohibited:

- Production deployment
- Public customer access
- Live trading
- Real-money investing
- Custody or movement of customer funds
- Passing untrusted glob or brace patterns through the affected lint tooling
- Executing Perl inside the API container
- Adding application dependencies or scripts that invoke Perl

This decision does not authorise production deployment, live trading, custody, investment
management, or handling real customer funds.

## Technical Evidence

### GHSA-mh99-v99m-4gvg / CVE-2026-14257

The affected dependency path is:

```text
packages/eslint-config
-> eslint
-> minimatch
-> brace-expansion@1.1.16
```

The package is used by development lint tooling and is not included in the Atlas production
runtime images. Forced patched-major and ESLint-major upgrades broke the supported lint-plugin
chain and were not retained.

### CVE-2026-12087

Docker Scout identified the affected Perl component in the official Python 3.12.13 slim base
image and reported no fixed Debian package at validation time. Atlas starts Uvicorn directly and
does not invoke Perl. The API runs non-root with a read-only root filesystem,
`no-new-privileges`, no host bind mounts, and no public deployment.

## Consequences

- Milestone 2 private development may proceed.
- Dependency and image scanning must continue.
- Both exceptions must be reviewed by 2026-08-27.
- Both exceptions expire on 2026-10-27 unless explicitly renewed through a new recorded decision.
- A compatible fix or fixed base image triggers immediate remediation and invalidates the relevant
  exception.
- Any production or public deployment requires independent security review and a new explicit
  production decision.

## Immediate Revocation Conditions

The relevant exception is revoked immediately if:

- the affected component becomes reachable from application runtime code or external input;
- untrusted input is passed to the affected lint tooling;
- Atlas begins invoking Perl directly or indirectly;
- a compatible patched dependency or fixed official base image becomes available;
- advisory severity or exploitability materially increases; or
- Atlas is prepared for public or production deployment.

## References

- [`docs/milestone-1-audit.md`](../milestone-1-audit.md)
- [`docs/security-risk-exceptions.md`](../security-risk-exceptions.md)
- [GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg)
- [CVE-2026-14257](https://nvd.nist.gov/vuln/detail/CVE-2026-14257)
- [CVE-2026-12087](https://nvd.nist.gov/vuln/detail/CVE-2026-12087)
