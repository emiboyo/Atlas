# Payments architecture

## Scope

Stripe is the external billing processor. Atlas stores only identifiers, lifecycle projections,
verified event envelopes, and explicit links to internal accounting entries. This foundation does
not create customers, Checkout Sessions, subscriptions, PaymentIntents, refunds, or charges.

## Components

- `BillingCustomer` maps one tenant to one Stripe Customer per Atlas environment.
- `BillingSubscription` projects Stripe product, price, status, and billing period state.
- `StripeWebhookEvent` is the durable, idempotent event inbox.
- `PaymentLedgerLink` connects a processed Stripe financial object to exactly one Atlas journal
  transaction without making Stripe the accounting source of truth.

## Webhook ingestion

`POST /api/v1/webhooks/stripe`:

1. limits payload size before and after reading;
2. reads the unmodified raw body;
3. verifies `Stripe-Signature` with the endpoint secret;
4. records the full verified event and SHA-256 payload digest;
5. deduplicates atomically on Stripe Event ID;
6. commits the inbox record;
7. returns `202` without performing downstream work.

Business processing belongs in a separate retryable worker. This keeps webhook latency low and
allows Stripe retries to be acknowledged safely. Events can arrive more than once or out of
order; processors must compare Stripe object state/version timestamps and remain idempotent.

## Subscription state

Atlas mirrors all documented Stripe subscription states, including incomplete, trialing, active,
past due, canceled, unpaid, and paused. A subscription projection is not itself an entitlement.
Access decisions will consume an independently derived entitlement projection once product and
commercial policies are approved.

## Accounting

Stripe objects never directly mutate balances. A payment-event processor will:

1. claim an inbox event with row locking;
2. resolve its tenant through the Stripe Customer mapping;
3. validate currency and minor-unit conversion;
4. create one balanced, idempotent ledger transaction;
5. insert a unique `PaymentLedgerLink`;
6. mark the event processed in the same database transaction.

Refunds, disputes, fees, tax, and chargebacks use new journal transactions and explicit clearing
accounts. Historical entries are never changed.

## Security and data handling

- Webhook secrets and API keys remain in managed secret stores.
- Raw request bodies must not be parsed before signature verification.
- Payloads are Confidential and require encryption, restricted access, and bounded retention.
- Payment method details, PAN, CVC, and bank credentials must never enter Atlas storage or logs.
- Live-mode and test-mode customer records must never share an environment.
- Endpoint secrets are different between Stripe CLI forwarding and registered endpoints.

## Processing states

Inbox states are `pending`, `processing`, `processed`, `failed`, and `ignored`. Workers must use
bounded retries, exponential backoff, dead-letter alerting, and stale-processing recovery. Error
fields contain stable codes only—never raw Stripe payload fragments or personal information.
