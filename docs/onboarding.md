# Identity Onboarding

## State machine

```text
not_started -> profile_required -> workspace_required -> completed
```

Provisioning creates a minimal profile in `profile_required` and an idempotent personal workspace.
The service verifies that both profile and personal workspace exist before moving to `completed`.
Repeated completion is safe.

Progress is stored in PostgreSQL, so refreshes and different browser sessions do not lose it.
Clients cannot submit `onboarding_status` directly because profile request schemas reject extra
fields.

## User experience

The protected onboarding route guides a user to confirm basic profile information, select locale,
IANA timezone, ISO-style country and base currency, confirm the personal workspace, and explicitly
complete onboarding.

## Explicit exclusions

Onboarding completion does not represent KYC completion, suitability, appropriateness,
investment approval, eligibility to trade, AML clearance, sanctions clearance, or regulatory
approval. No risk profiling or real KYC provider is implemented.

## Deactivation

Account deactivation requires the exact confirmation `DEACTIVATE` and a token issued within the
previous ten minutes. It changes the local lifecycle to `deactivated`, records an audit event, and
blocks future normal protected access. It does not hard-delete profiles, memberships, tenants,
audit history, ledger data, or future legally retained records. Privacy erasure is a separate
future workflow; this milestone does not claim GDPR erasure.
