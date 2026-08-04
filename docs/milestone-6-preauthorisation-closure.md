# Milestone 6A Pre-authorisation Closure Audit

> **Final closure status: READY FOR INDEPENDENT GOVERNANCE REVIEW**
>
> This audit does not authorise Milestone 6A implementation. ADR 0018 remains
> **PROPOSED — NOT YET AUTHORISED**.

## 1. Repository baseline

- Project root: `C:\Dev\Atlas`
- Branch: `chore/milestone-6-preauthorisation-closure`
- Baseline/HEAD at audit start: `6096bfb5e748242704f3a970e899c1d01b6d01db`
- Baseline merge: `merge: propose Milestone 6A governance boundary`
- Audit date: 2026-08-03
- Working tree at preflight: clean

ADR 0018 was present, uniquely numbered, unsigned, and stated both
`PROPOSED — NOT YET AUTHORISED` and
`NOT AUTHORISED UNTIL EXPLICITLY APPROVED`. No Milestone 6A application route,
API, model, migration, cloud telemetry, production-signing, tenant-data,
financial, AI, deployment, or product implementation was identified.

## 2. Evidence inventory

| Evidence                                       | Result                                                          |
| ---------------------------------------------- | --------------------------------------------------------------- |
| `clerk-key-revocation-attestation.md`          | Signed factual risk-owner testimony; independent review pending |
| `local-secret-inspection-redacted.txt`         | Created; local checks recorded without values                   |
| `node-production-audit.txt`                    | Created; command exit 0                                         |
| `node-development-audit.txt`                   | Created; command exit 0; governed advisory remains              |
| `node-dependency-path-redacted.txt`            | Created; exact development dependency path recorded             |
| `python-dependency-audit.txt`                  | Created; command exit 0; no known vulnerabilities               |
| `docker-scout-api-full.txt`                    | Replaced by successful authenticated full-image scan            |
| `docker-scout-cve-2026-12087.txt`              | Updated; targeted scan confirms one Critical finding            |
| `container-remediation-report.md`              | Created; container findings reduced, residual review required   |
| `milestone-6a-security-exception-proposals.md` | Created; five separate unsigned proposals                       |

## 3. Clerk incident evidence

The risk owner states that both exposed Atlas Clerk Development secret keys
were deleted, only one rotated Development secret remains active, and Atlas
successfully authenticated after rotation. The signed factual attestation
records this testimony without a secret value, complete identifier,
publishable key, or retained screenshot.

This is risk-owner testimony, not independently verified provider evidence.
The risk owner signed the factual attestation on 2026-08-03. M6-R006 remains
open pending independent review of the provider-verification limitation. The
absence of completed independent acceptance does not prevent the evidence
package from being ready for independent governance review.

## 4. Local secret-search evidence

`git check-ignore` confirmed `apps/web/.env.local` and root `.env` are ignored.
`git ls-files` confirmed neither file is tracked. A value-redacted pattern scan
found:

- current tracked tree: zero secret-pattern locations;
- Git history: two possible pattern locations at commit `d39d373210fb`, confined
  to `apps/api/.env.example` and `apps/web/.env.example`;
- current versions of those tracked example files: no matching location.

The historical locations are recorded without values. Their example-template
context does not prove an active provider credential, and it does not replace
provider revocation evidence.

## 5. Image and log secret inspection

Pattern-only inspection recorded zero matching lines/files in:

- `atlas-ai-web` image configuration;
- Docker image history;
- the final runtime filesystem under `/app`; and
- current Compose web logs.

The inspection did not print or compare a configured secret value. It did not
perform forensic recovery of deleted content from every compressed layer, so
an independent image/layer scan remains required before closure.

## 6. Node production audit

`pnpm audit:governed:prod` exited 0. The repository policy reports the governed
development advisory but identifies no affected production runtime dependency.
This pass does not close the development finding.

## 7. Node development audit

`pnpm audit:governed` exited 0 under the governed exception policy and reported
that GHSA-mh99-v99m-4gvg / CVE-2026-14257 remains. Installed evidence shows:

```text
@atlas/eslint-config
  -> eslint 9.39.5
  -> minimatch 3.1.5
  -> brace-expansion 1.1.16
```

The path is development/CI lint tooling. No production web or API runtime path
was identified. Exploitability requires untrusted brace patterns to reach the
toolchain. Other unrelated paths use `brace-expansion` 5.0.8, but the ESLint
path remains affected and no compatible validated replacement was established.

## 8. Python dependency audit

`python -m pip_audit -r apps/api/requirements.txt` exited 0 and reported no
known vulnerabilities in the pinned Python packages. This package-level result
does not inspect operating-system packages in the API image and therefore does
not resolve CVE-2026-12087.

## 9. Docker Scout API image scan

The running API container resolved successfully to local image `atlas-ai-api`.
After Docker authentication, both required `local://atlas-ai-api` scans exited
0 and wrote replacement evidence. The original scan analysed digest prefix
`eaa9889761b6`, platform `linux/amd64`, size 82 MB, and 171 packages.

The full scan reported 46 findings across 12 packages: 2 Critical, 2 High, 8
Medium, 29 Low, and 5 of unspecified severity. The Critical findings were
CVE-2026-13221 and CVE-2026-12087 in Perl 5.40.1-6. The High findings were
CVE-2026-48959 and CVE-2026-48962 in the same package. Scout reported no fixed
Debian package version for these four findings.

The targeted scan confirmed exactly one Critical CVE-2026-12087 finding in
`perl 5.40.1-6`, with evidence in the Debian package metadata/image layers and
`Fixed version: not fixed`. Scout describes the vulnerable `Socket.xs`
`pack_ip_mreq_source()` path as requiring a Perl script to pass an undersized,
attacker-controlled source value. Atlas does not invoke Perl, but absence of
current application reachability is a compensating control, not remediation.

The current official base was rebuilt from committed Dockerfile source
`a8db1a0f627365c94bdd605548bab0cee0e32128` with `--pull --no-cache`. Atlas does not
install Perl; it is inherited from `python:3.12.13-slim`. Removing runtime
`pip` and its vendored build tooling reduced a refreshed intermediate image
from 2 Critical/4 High, 82 MB, and 186 indexed packages to 2 Critical/2 High,
79 MB, and 170 packages at current digest prefix `99a3d38d6dd9`. The remaining four
findings are exclusively in inherited Perl 5.40.1-6. The API remained healthy,
Alembic remained at head, all 139 tests passed against PostgreSQL with 86.01%
coverage, and the Python dependency audit remained clean.

Official `python:3.12.13-slim-bookworm` retains the same four Perl findings.
Scout's Python 3.13/3.14 slim recommendations also retain them. Alpine would
change the libc and recommended Python minor version and was not adopted
without separate compatibility qualification. See
`docs/evidence/milestone-6a/container-remediation-report.md`.

Scout also warned that it could not delete one temporary archive because the
file was in use. The scan and reports nevertheless completed successfully. The
temporary-cleanup warning requires local housekeeping but does not invalidate
the indexed result.

## 10. Governed advisory status

### GHSA-mh99-v99m-4gvg / CVE-2026-14257

- Current presence: present as `brace-expansion` 1.1.16.
- Dependency path: ESLint 9.39.5 / minimatch 3.1.5 development tooling.
- Reachability: development and CI linting; not identified in production runtime.
- Exploitability: requires attacker-controlled brace patterns reaching tooling.
- Fixed-version availability: newer package lines exist, but no compatible,
  validated fix for the installed ESLint path was established.
- Compensating controls: no untrusted patterns; lint excluded from runtime; no
  production deployment; continued audit; revoke exception on reachability/fix.
- Closure decision: cannot close.
- Exception need: explicit Milestone 6A-only risk-owner decision required.
- Proposed owner: Adebayo Olaegbe.
- Proposed review/expiry: 2026-08-17 / no later than 2026-10-27.
- Immediate stop: runtime reachability, untrusted input, compatible fix,
  increased severity/exploitability, public/production use, or expired decision.

### CVE-2026-12087

- Current presence: confirmed Critical in the scanned current local image.
- Affected component: `perl 5.40.1-6` inherited from the official Python slim
  operating-system layer.
- Dependency path: operating-system layer, not Python requirements.
- Reachability/exploitability: Atlas does not invoke Perl; exploitation requires
  the affected component to become reachable.
- Fixed-version availability: Docker Scout reports `not fixed` for the Debian
  package in the current image; the report references an upstream Perl fix in
  v5.43.11 but no installable image/package remediation.
- Compensating controls: no Perl invocation; non-root API; read-only root
  filesystem; `no-new-privileges`; no host bind mounts; no production use.
- Closure decision: cannot close.
- Exception need: remains required unless a rebuilt current image proves
  absence/fix; any extension must explicitly name Milestone 6A.
- Proposed owner: Adebayo Olaegbe.
- Proposed review/expiry: 2026-08-17 / no later than 2026-10-27.
- Immediate stop: component becomes reachable, Perl is invoked, fixed official
  image becomes available, severity/exploitability increases, public/production
  use begins, or the decision expires.

## 11. Proposed exception decisions

`docs/milestone-6a-security-exception-proposals.md` contains five separate
decisions: M6A-EX-001 for the Node advisory and M6A-EX-002 through M6A-EX-005
for each Perl CVE. Every decision is **PROPOSED — NOT ACCEPTED**, has separate
technical and scope analysis, and contains unsigned independent-review and
risk-owner fields.

All are restricted to Milestone 6A local/CI operational evidence work using
synthetic data only. No proposal silently extends the Milestone 5 decisions or
authorises production, public access, sensitive/financial data, external AI,
live providers, payments, trading, execution, custody, real money, customer
funds, or activity outside ADR 0018. M6-R004 remains open with proposed
exception decisions prepared.

## 12. Unresolved blockers

1. Independent review of the signed Clerk Development-key revocation
   attestation and its provider-verification limitation.
2. Independent validation that no complete secret or sensitive identifier is
   present in retained evidence or the proposed decisions.
3. Independent validation of the authenticated remediated-image scan and explicit disposition
   of CVE-2026-12087 plus the additional Critical/High image findings
   CVE-2026-13221, CVE-2026-48959, and CVE-2026-48962.
4. Validated fix or explicit signed Milestone 6A decision for
   GHSA-mh99-v99m-4gvg / CVE-2026-14257.
5. Validated closure or separate explicit signed Milestone 6A decisions for
   CVE-2026-13221, CVE-2026-12087, CVE-2026-48959, and CVE-2026-48962.
6. Independent reviewer acceptance of Clerk, dependency, container, secret,
   scope, and compensating-control evidence.
7. Completed risk-owner decision, conditions, reviewers, dates, expiry, and
   signature in ADR 0018.

## 13. Independent-review requirements

An independent reviewer must inspect the signed factual Clerk attestation and its
provider-verification limitation, repeat secret scans without exposing values, authenticate Docker Scout and
verify the exact current image digest, validate advisory reachability and fixed
versions, review exception wording, confirm M6-R004/M6-R006 disposition, and
verify that the only non-documentation change is the reviewed API runtime-tool
cleanup. The reviewer must not treat a governed audit exit 0 as proof that its
acknowledged exception is resolved.

## 14. Governance-document status

`docs/security-risk-exceptions.md`, `docs/milestone-6-governance.md`,
`docs/milestone-6-risk-register.md`, and ADR 0018 now cross-reference the
unsigned proposals and signed factual attestation. M6-R004 is open with proposed decisions
prepared. M6-R006 is open with the factual risk-owner attestation provided and
independent limitation review required. No risk is accepted; ADR 0018 remains
unsigned and proposed.

## 15. Final closure status

**READY FOR INDEPENDENT GOVERNANCE REVIEW**

All five proposed exceptions, current container evidence, and the signed
factual Clerk attestation are documented. Secret-pattern checks found no value
in the evidence or diff; every proposed decision remains unsigned; ADR 0018
remains proposed; and no Milestone 6A product implementation began. Independent
review must occur before risk-owner acceptance/signature. Milestone 6A
implementation remains prohibited until separate final approval.
