# ADR 0004: Stripe webhook inbox and accounting boundary

- Status: Accepted
- Date: 2026-07-24

## Context

Stripe billing activity is asynchronous. Events can be duplicated, retried, and delivered out of
order. Performing billing mutations directly in an HTTP webhook handler risks timeouts, replay
bugs, and inconsistent accounting.

## Decision

Verify Stripe signatures against the unmodified request body, then atomically insert events into
a durable inbox keyed by Stripe Event ID. Return `202` after persistence. A separate worker will
process inbox events idempotently. Stripe customer and subscription records are projections;
Atlas's balanced ledger remains the financial source of truth. Each processed Stripe financial
object can link to only one internal ledger transaction.

## Consequences

Webhook delivery is fast and replay-safe. Processing is eventually consistent and requires queue
latency monitoring, retries, dead-letter handling, reconciliation, and payload retention policy.
Financial effects require explicit event handlers and accounting rules before activation.
