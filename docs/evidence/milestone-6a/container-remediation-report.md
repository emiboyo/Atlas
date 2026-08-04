# Milestone 6A API Container Remediation Report

> **Status: CONTAINER FINDINGS REDUCED — RESIDUAL REVIEW REQUIRED**
>
> This report does not accept any security exception or authorise Milestone 6A.
> ADR 0018 remains **PROPOSED — NOT YET AUTHORISED**.

## Scope

This focused remediation assessed only the Atlas API container. It did not
change application behaviour, routes, authentication, database models,
migrations, financial functionality, AI functionality, or deployment
configuration.

## Root cause

The API uses `python:3.12.13-slim` for both builder and runtime stages. Atlas
does not install an operating-system package in either stage. Perl 5.40.1-6 is
introduced by the official Debian Trixie-based Python image, before any Atlas
layer. Atlas runtime code and startup commands do not invoke Perl.

The existing multi-stage build already confines dependency installation to the
builder and copies only the virtual environment into the runtime. The copied
virtual environment nevertheless retained `pip` and its vendored development
packages. A refreshed build exposed two additional High findings in that
runtime build tooling.

## Remediation

The builder now removes `pip` after installing the pinned application
requirements. `setuptools` is included in the removal command defensively but
was not installed in the virtual environment. The final runtime therefore does
not contain `pip`, its vendored `msgpack`, or its vendored `setuptools` data.
No application dependency was removed.

Perl was not removed. Debian marks `perl-base` as `Essential: yes` and
`Priority: required`; it is inherited from the base layer, and Scout reports no
fixed Debian package for the four findings. Deleting an essential base package
or its files without a supported package transition would not be a safe
remediation.

## Image evidence

| Point                                 | Digest                                                             |  Size | Indexed packages |      Critical/High |
| ------------------------------------- | ------------------------------------------------------------------ | ----: | ---------------: | -----------------: |
| Original authenticated image          | `eaa9889761b6766e883c436e9b533fbc0bbe4328310b88c7a30ab94e6d8b3f32` | 82 MB |              171 | 2 Critical, 2 High |
| Refreshed base before tooling removal | `54a3cb05b1447e17a1a1917bc587b712d9c0eee83ead9f84e3e368aac7cc09a8` | 82 MB |              186 | 2 Critical, 4 High |
| Initial remediated runtime            | `62cf21a8719ebb8915b9a4943c613e05bd78f2293dc36cceb5af82418130e6c9` | 79 MB |              170 | 2 Critical, 2 High |
| Committed-source regenerated runtime  | `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb` | 79 MB |              170 | 2 Critical, 2 High |

The current committed-source scan, rebuilt from Dockerfile commit `a8db1a0`,
contains only these Critical/High findings, all attributed to inherited Perl
5.40.1-6:

- CVE-2026-13221 — Critical — no fixed Debian package reported.
- CVE-2026-12087 — Critical — no fixed Debian package reported.
- CVE-2026-48959 — High — no fixed Debian package reported.
- CVE-2026-48962 — High — no fixed Debian package reported.

The runtime-tool cleanup removed the refreshed image's High findings
GHSA-6v7p-g79w-8964 in vendored `msgpack` and CVE-2025-47273 in vendored
`setuptools`. It did not and cannot resolve the base-image Perl findings.

## Base-image evaluation

Docker Scout reported the current Python 3.12 slim image is up to date. Its
Python 3.13 and 3.14 slim recommendations retain 2 Critical and 2 High
findings, while also changing the supported Python minor version. A direct
scan of official `python:3.12.13-slim-bookworm` also reported the same four
Perl findings, so it offers no reduction.

Scout lists Alpine without known findings, but adopting it would replace glibc
with musl and change the recommended tag to Python 3.14. That is a material
runtime compatibility change requiring separate dependency, performance, and
operational qualification. It was not forced into this container-only fix.

## Runtime and security validation

- Clean build: `docker compose build --pull --no-cache api` — passed.
- Recreate: `docker compose up --detach --force-recreate api` — passed.
- Container status: healthy.
- Live endpoint: HTTP 200, healthy.
- Ready endpoint: HTTP 200; PostgreSQL and Redis healthy.
- Alembic current: `20260730_0008 (head)`.
- Runtime `pip`: confirmed absent.
- Runtime user: `atlas`.
- Read-only root filesystem: enabled.
- `no-new-privileges`: enabled.
- Container mounts: none; consequently zero host bind mounts.
- Source commit: `a8db1a0f627365c94bdd605548bab0cee0e32128`.
- Current image digest: `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`.
- Python suite: 139 passed against isolated real PostgreSQL.
- Coverage: 86.01%; required threshold 80%.
- `pip check`: no broken requirements.
- `pip-audit -r apps/api/requirements.txt`: no known vulnerabilities.

The committed-source rerun used an ephemeral PostgreSQL 16.9 container bound
only to `127.0.0.1:55460`, applied migrations through 0008, passed all 139
tests, and removed the ephemeral container afterward.

Historically, the first test run omitted `ATLAS_TEST_DATABASE_URL`, skipped 43 PostgreSQL
tests, and failed the coverage gate at 65.98%. The next attempted host URL was
invalid because Compose intentionally does not publish PostgreSQL. The final
corrected runs used isolated PostgreSQL and passed.

## Residual risk and recommendation

All four residual findings require separate governance triage. Current
compensating controls are absence of Perl invocation, non-root execution,
read-only root filesystem, `no-new-privileges`, no mounts, private development
only, and prohibition on production deployment. These controls reduce
reachability; they do not remediate the affected package.

Do not accept or downgrade the findings. If no supported fixed official base
becomes available before authorisation review, prepare separate, signed,
time-bounded Milestone 6A-only decisions for CVE-2026-13221,
CVE-2026-12087, CVE-2026-48959, and CVE-2026-48962. Revoke each decision when a
fixed supported base becomes available, Perl becomes reachable, severity or
exploitability changes, or the private-development boundary changes.

## Evidence files

- `docker-scout-recommendations.txt`
- `docker-scout-api-critical-high.txt`
- `docker-scout-cve-2026-12087.txt`
- `docker-scout-python-3.12.13-slim-bookworm-critical-high.txt`
- `container-remediation-python-tests.txt`
- `container-remediation-python-audit.txt`

## Final status

**CONTAINER FINDINGS REDUCED — RESIDUAL REVIEW REQUIRED**
