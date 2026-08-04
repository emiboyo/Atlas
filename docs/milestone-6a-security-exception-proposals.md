# Milestone 6A Security Exception Proposals

> **Package status: PROPOSED — NOT ACCEPTED**
>
> These proposals are prepared for independent governance review. No exception
> is accepted, no signature is present, and Milestone 6A implementation remains
> prohibited under ADR 0018.

## Common scope boundary

Every proposal below is limited to **Milestone 6A local/CI operational evidence
work using synthetic data only**. Each prohibits production, public access,
tenant data, personal data, portfolio data, research data, financial data,
external AI, live providers, payments, trading, execution, custody, real money,
customer funds, and every activity outside ADR 0018.

The governance sequence is evidence and proposed exceptions first, independent
review second, risk-owner acceptance and signature third, and implementation
only after final approval. A proposal, review, or technical validation is not
risk acceptance.

## M6A-EX-001 — GHSA-mh99-v99m-4gvg / CVE-2026-14257

- **Status:** PROPOSED — NOT ACCEPTED
- **Affected component/version:** `brace-expansion` 1.1.16.
- **Exact path:** `@atlas/eslint-config -> eslint 9.39.5 -> minimatch 3.1.5 -> brace-expansion 1.1.16`.
- **Severity:** High.
- **Current presence evidence:** `docs/evidence/milestone-6a/node-development-audit.txt` and `node-dependency-path-redacted.txt`.
- **Runtime reachability:** No web or API production-runtime path identified; the package is confined to development/CI lint tooling.
- **Exploitability prerequisites:** An untrusted attacker-controlled brace pattern must reach the affected lint/minimatch path.
- **Fixed-version status:** Patched package lines exist, but no compatible validated replacement for the installed ESLint/plugin chain was established.
- **Remediation attempted:** Governed dependency audit and dependency-path analysis; earlier forced incompatible upgrades broke the lint chain.
- **Why further remediation was not selected:** An unvalidated override would break or weaken required lint controls; replacement remains mandatory when compatible.
- **Compensating controls:** Lint tooling excluded from application runtime; no untrusted brace pattern may reach lint/minimatch; development/CI use only; governed dependency audit on every relevant change; replace or remove when a compatible fix is available; no elevated secrets for untrusted workflow changes.
- **Permitted scope:** Milestone 6A local/CI operational evidence work using synthetic data only.
- **Prohibited scope:** Production; public access; tenant, personal, portfolio, research, or financial data; external AI; live providers; payments; trading; execution; custody; real money; customer funds; all scope outside ADR 0018.
- **Owner:** Adebayo Olaegbe.
- **Proposed review date:** 2026-08-17.
- **Proposed expiry:** No later than 2026-10-27.
- **Monitoring:** Run the governed Node dependency audit on every relevant dependency or lint-tooling change and before approval; record the exact path and version.
- **Immediate revocation:** Runtime reachability; untrusted brace input; compatible fix; increased severity/exploitability; audit failure; public/production use; prohibited data or scope; review/expiry lapse.
- **Independent reviewer:** _Required._
- **Independent review decision/date:** _Required._
- **Risk-owner decision:** _Required — accept, reject, or require remediation._
- **Risk-owner signature/date:** _Required._

## M6A-EX-002 — CVE-2026-13221

- **Status:** PROPOSED — NOT ACCEPTED
- **Affected component/version:** Debian `perl` 5.40.1-6, inherited from the official Python slim base image. Docker Scout evidence includes files supplied through the associated `perl-base` package.
- **Exact path:** Official `python:3.12.13-slim` runtime base -> Debian 13 Trixie base layer -> `perl-base` 5.40.1-6.
- **Severity:** Critical.
- **Current presence evidence:** Remediated image digest `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`; `docker-scout-api-critical-high.txt`.
- **Runtime reachability:** Atlas starts Uvicorn directly and does not invoke Perl or a Perl script.
- **Exploitability prerequisites:** Perl execution and compilation of attacker-controlled regular-expression input containing more than 65,535 fixed-string alternation branches.
- **Fixed-version status:** Scout reports no fixed Debian package for the selected image; it references an upstream fix after the installed version.
- **Remediation attempted:** Pulled and rebuilt the current base without cache; removed unnecessary runtime packaging tools; scanned Python 3.12 Bookworm and reviewed Scout's supported slim recommendations.
- **Why further remediation was not selected:** Bookworm and newer slim recommendations retain the finding; `perl-base` is Debian Essential/required; Alpine changes libc and Python compatibility and requires separate qualification.
- **Compensating controls:** Atlas must not invoke Perl; no Perl script execution; no attacker-controlled Perl regex, Socket arguments, archive, zip, or glob input; non-root execution; read-only root filesystem; `no-new-privileges`; no mounts; private development only; re-scan before approval and whenever the base changes; rebuild promptly when a supported fixed image is available.
- **Permitted scope:** Milestone 6A local/CI operational evidence work using synthetic data only.
- **Prohibited scope:** Production; public access; tenant, personal, portfolio, research, or financial data; external AI; live providers; payments; trading; execution; custody; real money; customer funds; all scope outside ADR 0018.
- **Owner:** Adebayo Olaegbe.
- **Proposed review date:** 2026-08-17.
- **Proposed expiry:** No later than 2026-10-27.
- **Monitoring:** Authenticated Critical/High image scan before approval, on every base-image change, and at review; monitor supported fixed-image availability.
- **Immediate revocation:** Perl invocation or script execution; attacker-controlled Perl input; component reachability; fixed supported image; increased severity/exploitability; failed scan/control; prohibited use; review/expiry lapse.
- **Independent reviewer:** _Required._
- **Independent review decision/date:** _Required._
- **Risk-owner decision:** _Required — accept, reject, or require remediation._
- **Risk-owner signature/date:** _Required._

## M6A-EX-003 — CVE-2026-12087

- **Status:** PROPOSED — NOT ACCEPTED
- **Affected component/version:** Debian `perl` 5.40.1-6, inherited from the official Python slim base image. Docker Scout evidence includes files supplied through the associated `perl-base` package.
- **Exact path:** Official `python:3.12.13-slim` runtime base -> Debian 13 Trixie base layer -> `perl-base` 5.40.1-6.
- **Severity:** Critical.
- **Current presence evidence:** Remediated image digest `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`; `docker-scout-cve-2026-12087.txt` and `docker-scout-api-critical-high.txt`.
- **Runtime reachability:** Atlas does not invoke Perl or `Socket::pack_ip_mreq_source`.
- **Exploitability prerequisites:** A Perl script must pass an undersized attacker-controlled source argument to the affected Socket function.
- **Fixed-version status:** Scout reports no fixed Debian package for the selected image and references upstream Socket/Perl remediation unavailable in the supported base.
- **Remediation attempted:** Current base refresh, no-cache rebuild, removal of runtime packaging tools, Bookworm scan, and supported-image recommendation review.
- **Why further remediation was not selected:** Same-version Bookworm retains the finding; `perl-base` is Essential/required; deleting it is unsupported; Alpine requires separate compatibility qualification.
- **Compensating controls:** Atlas must not invoke Perl; no Perl script execution; no attacker-controlled Perl regex, Socket arguments, archive, zip, or glob input; non-root execution; read-only root filesystem; `no-new-privileges`; no mounts; private development only; re-scan before approval and whenever the base changes; rebuild promptly when a supported fixed image is available.
- **Permitted scope:** Milestone 6A local/CI operational evidence work using synthetic data only.
- **Prohibited scope:** Production; public access; tenant, personal, portfolio, research, or financial data; external AI; live providers; payments; trading; execution; custody; real money; customer funds; all scope outside ADR 0018.
- **Owner:** Adebayo Olaegbe.
- **Proposed review date:** 2026-08-17.
- **Proposed expiry:** No later than 2026-10-27.
- **Monitoring:** Targeted and Critical/High authenticated scan before approval, on every base-image change, and at review; monitor fixed-image availability.
- **Immediate revocation:** Perl or Socket invocation; attacker-controlled arguments; component reachability; fixed supported image; increased severity/exploitability; failed scan/control; prohibited use; review/expiry lapse.
- **Independent reviewer:** _Required._
- **Independent review decision/date:** _Required._
- **Risk-owner decision:** _Required — accept, reject, or require remediation._
- **Risk-owner signature/date:** _Required._

## M6A-EX-004 — CVE-2026-48959

- **Status:** PROPOSED — NOT ACCEPTED
- **Affected component/version:** Debian `perl` 5.40.1-6, inherited from the official Python slim base image. Docker Scout evidence includes files supplied through the associated `perl-base` package.
- **Exact path:** Official `python:3.12.13-slim` runtime base -> Debian 13 Trixie base layer -> `perl-base` 5.40.1-6.
- **Severity:** High.
- **Current presence evidence:** Remediated image digest `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`; `docker-scout-api-critical-high.txt`.
- **Runtime reachability:** Atlas does not invoke Perl, IO::Uncompress, or a Perl archive-processing script.
- **Exploitability prerequisites:** Perl execution that processes an attacker-supplied ZIP archive and seeks a named entry through the affected fast-forward path.
- **Fixed-version status:** Scout reports no fixed Debian package for the selected image and references an upstream IO::Compress fix unavailable in it.
- **Remediation attempted:** Current base refresh, no-cache rebuild, removal of runtime packaging tools, Bookworm scan, and supported-image recommendation review.
- **Why further remediation was not selected:** Supported Debian slim alternatives retain the finding; essential package deletion is unsafe; Alpine requires separate compatibility qualification.
- **Compensating controls:** Atlas must not invoke Perl; no Perl script execution; no attacker-controlled Perl regex, Socket arguments, archive, zip, or glob input; non-root execution; read-only root filesystem; `no-new-privileges`; no mounts; private development only; re-scan before approval and whenever the base changes; rebuild promptly when a supported fixed image is available.
- **Permitted scope:** Milestone 6A local/CI operational evidence work using synthetic data only.
- **Prohibited scope:** Production; public access; tenant, personal, portfolio, research, or financial data; external AI; live providers; payments; trading; execution; custody; real money; customer funds; all scope outside ADR 0018.
- **Owner:** Adebayo Olaegbe.
- **Proposed review date:** 2026-08-17.
- **Proposed expiry:** No later than 2026-10-27.
- **Monitoring:** Authenticated Critical/High scan before approval, on every base-image change, and at review; monitor the Debian and official Python image channels.
- **Immediate revocation:** Perl/archive invocation; attacker-controlled ZIP/archive input; component reachability; fixed supported image; increased severity/exploitability; failed scan/control; prohibited use; review/expiry lapse.
- **Independent reviewer:** _Required._
- **Independent review decision/date:** _Required._
- **Risk-owner decision:** _Required — accept, reject, or require remediation._
- **Risk-owner signature/date:** _Required._

## M6A-EX-005 — CVE-2026-48962

- **Status:** PROPOSED — NOT ACCEPTED
- **Affected component/version:** Debian `perl` 5.40.1-6, inherited from the official Python slim base image. Docker Scout evidence includes files supplied through the associated `perl-base` package.
- **Exact path:** Official `python:3.12.13-slim` runtime base -> Debian 13 Trixie base layer -> `perl-base` 5.40.1-6.
- **Severity:** High.
- **Current presence evidence:** Remediated image digest `99a3d38d6dd9f8c69b9579593007f4720502b0bc1bb836cf0215b6cf4f4baabb`; `docker-scout-api-critical-high.txt`.
- **Runtime reachability:** Atlas does not invoke Perl, File::GlobMapper, or Perl glob-processing scripts.
- **Exploitability prerequisites:** Perl execution with an attacker-controlled output glob reaching the affected string-evaluation path.
- **Fixed-version status:** Scout reports no fixed Debian package for the selected image and references an upstream IO::Compress fix unavailable in it.
- **Remediation attempted:** Current base refresh, no-cache rebuild, removal of runtime packaging tools, Bookworm scan, and supported-image recommendation review.
- **Why further remediation was not selected:** Supported Debian slim alternatives retain the finding; essential package deletion is unsafe; Alpine requires separate compatibility qualification.
- **Compensating controls:** Atlas must not invoke Perl; no Perl script execution; no attacker-controlled Perl regex, Socket arguments, archive, zip, or glob input; non-root execution; read-only root filesystem; `no-new-privileges`; no mounts; private development only; re-scan before approval and whenever the base changes; rebuild promptly when a supported fixed image is available.
- **Permitted scope:** Milestone 6A local/CI operational evidence work using synthetic data only.
- **Prohibited scope:** Production; public access; tenant, personal, portfolio, research, or financial data; external AI; live providers; payments; trading; execution; custody; real money; customer funds; all scope outside ADR 0018.
- **Owner:** Adebayo Olaegbe.
- **Proposed review date:** 2026-08-17.
- **Proposed expiry:** No later than 2026-10-27.
- **Monitoring:** Authenticated Critical/High scan before approval, on every base-image change, and at review; monitor the Debian and official Python image channels.
- **Immediate revocation:** Perl/glob invocation; attacker-controlled glob input; component reachability; fixed supported image; increased severity/exploitability; failed scan/control; prohibited use; review/expiry lapse.
- **Independent reviewer:** _Required._
- **Independent review decision/date:** _Required._
- **Risk-owner decision:** _Required — accept, reject, or require remediation._
- **Risk-owner signature/date:** _Required._

## Package decision fields

- Independent security reviewer: _Required_
- Independent reliability/governance reviewer: _Required_
- Review date: _Required_
- Reviewer conclusion: _Required_
- Risk-owner package decision: _Required_
- Risk-owner signature: _Required_
- Decision date: _Required_

Until each relevant decision field is completed and ADR 0018 receives separate
final approval, these proposals grant no authority.
