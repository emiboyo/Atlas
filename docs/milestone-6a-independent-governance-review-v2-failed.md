# Milestone 6A Independent Governance Review V2

> **Final decision: INDEPENDENT REVIEW FAILED — NOT READY FOR RISK-OWNER DECISION**

## Baseline

- Branch: `audit/milestone-6a-independent-governance-review-v2`
- Commit: `62fd41ec2dd32c8216f774508e7371aa37753427`
- Scope review: Passed
- Clerk incident review: Rejected

## Blocking finding

The running web container exposes a non-empty `CLERK_SECRET_KEY` entry through
Docker container configuration `.Config.Env`.

No secret value was printed or retained during the review.

This contradicts the package's supporting local-secret evidence and leaves the
current rotated Clerk Development secret unnecessarily exposed to anyone with
sufficient Docker inspection access.

## Required remediation

1. Remove `CLERK_SECRET_KEY` from Compose `environment` and `env_file`
   injection.
2. Supply it through a Docker Compose secret mounted under `/run/secrets`.
3. Ensure the secret does not exist in image configuration or container
   `.Config.Env`.
4. Rotate the currently configured Clerk Development secret after remediation.
5. Rebuild and recreate the web container.
6. Repeat repository, image, container-configuration, filesystem and log scans.
7. Regenerate the closure evidence from committed source.
8. Conduct a new independent review from a clean baseline.

## Review status

- Clerk limitation verdict: **REJECTED**
- Security exceptions: No reviewer decision
- ADR 0018: **PROPOSED — NOT YET AUTHORISED**
- Milestone 6A implementation: Prohibited

The review stopped when the blocking secret-exposure finding was confirmed.
