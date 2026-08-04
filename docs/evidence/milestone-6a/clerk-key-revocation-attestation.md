# Clerk Development-Key Revocation Attestation

> **Status: RISK-OWNER ATTESTATION PROVIDED — INDEPENDENT REVIEW PENDING**
>
> This document records risk-owner testimony. The stated provider state has not
> been independently verified directly against Clerk provider records.

## Instance and incident

- Application: Atlas AI
- Clerk environment: Development
- Evidence-package date: 2026-08-03
- Risk owner: Adebayo Olaegbe

## Risk-owner statement

I attest that both Atlas Clerk Development secret keys exposed during local
development were deleted in the Clerk provider dashboard, and that only one
rotated Development secret key remains active. I further attest that Atlas
successfully authenticated after the rotation.

This attestation contains no secret value, complete key identifier,
publishable key, or provider screenshot. No screenshot containing sensitive
information will be retained as evidence.

## Independent-review limitation

The repository, Git-history, image, runtime-filesystem, and log checks provide
supporting local evidence but cannot prove provider-side deletion or current
provider state. An independent reviewer must assess whether this signed
testimony and the supporting local evidence are sufficient for the bounded
Milestone 6A decision. The reviewer is not represented as having inspected the
Clerk dashboard or provider records.

## Immediate action if inaccurate

If any part of this statement is later found inaccurate, Atlas must immediately
stop Milestone 6A work, revoke every affected Clerk Development secret, rotate
to a new Development secret, repeat repository/history/image/log checks without
recording secret values, assess unauthorised use, and obtain a new independent
review before work resumes. Production and public access remain prohibited.

## Signature

- Risk owner: Adebayo Olaegbe
- Risk-owner decision: Confirmed
- Risk-owner signature: Adebayo Olaegbe
- Decision date: 2026-08-03
- Independent limitation reviewer: _Required_
- Independent review date: _Required_
- Reviewer conclusion: _Required_

This signature confirms only the factual risk-owner statement above. The
independent-review fields remain incomplete. This attestation does not accept a
security exception, approve ADR 0018, or authorise Milestone 6A implementation.
