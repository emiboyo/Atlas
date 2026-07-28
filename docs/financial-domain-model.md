# Financial domain model

## Purpose

This model establishes durable identity, ownership, instrument, portfolio, position, and
accounting boundaries. Milestone 4 adds simulated valuation and descriptive historical
analytics. It does not implement order execution, recommendations, suitability, prediction, or
real investment behavior.

## Aggregate boundaries

### Identity and tenancy

- `Tenant` maps exactly one internal tenant to one Clerk Organization.
- `User` maps an internal subject to a Clerk user.
- `Membership` records the local projection of organization membership and role.

Clerk remains the authentication source. Internal identifiers remain stable if an external
provider mapping changes. Every tenant-owned financial table carries `tenant_id`.

### Instruments

- `Instrument` is the canonical economic asset.
- `InstrumentListing` represents a tradable venue, ticker, quote currency, and price increment.

ISIN and FIGI are optional but globally unique when present. Venue MIC and currencies use
fixed-width identifiers. Metadata is explicitly versioned so provider corrections can be audited.

### Accounts and portfolios

- `InvestmentAccount` represents the legal or provider account boundary.
- `Portfolio` is an allocation and reporting boundary within an account.
- `PositionSnapshot` is an immutable, point-in-time derived state.

Positions are snapshots rather than the source of truth. Future holdings are reconstructed from
settled events and ledger activity, then materialized for query performance. Quantities and cost
bases use `NUMERIC(38,18)`; binary floating point is forbidden.

### Ledger

- `LedgerAccount` is a currency-specific chart-of-accounts node.
- `LedgerTransaction` groups an idempotent journal event.
- `LedgerEntry` is an immutable signed posting.

A positive or negative signed amount represents the account movement. Posted transactions:

1. contain at least two entries;
2. sum to zero independently for each currency;
3. cannot have entries updated or deleted;
4. use a tenant-scoped idempotency key;
5. are corrected through new reversal transactions, never destructive edits.

PostgreSQL deferred constraint triggers enforce balance at transaction commit, allowing all
entries to be inserted atomically before validation.

## Tenant isolation

Composite foreign keys include `tenant_id` wherever one tenant-owned record references another.
This prevents cross-tenant references at the database level. Future repository methods must
still require tenant context and production deployments should add PostgreSQL row-level security
as defence in depth after the connection and migration roles are separated.

## Lifecycle policy

- Financial journals and position snapshots are append-only.
- Accounts and tenants use explicit lifecycle states rather than deletion.
- Reference data can be made inactive or delisted without erasing history.
- Retention and legal-hold policies will be applied by classification and jurisdiction.
- Timestamps are stored as timezone-aware UTC values.

## Explicitly deferred

- Tax-lot accounting and jurisdiction-specific cost basis
- Corporate actions and symbol/identifier history
- Orders, executions, allocations, settlement, and custody reconciliation
- FX valuation and reporting-currency translation
- Fractional-share rounding and residual handling
- Performance measurement and benchmark methodology
- Suitability, appropriateness, KYC, AML, sanctions, and tax residency workflows

These require approved provider, legal, accounting, and regulatory rules before implementation.

## Milestone 4 simulated extension

The original `Portfolio` and signed-ledger aggregates are extended rather than duplicated.
`PortfolioAccount` maps currency-specific simulated roles onto existing ledger accounts.
`PortfolioTransaction` is ordered, idempotent, immutable paper activity.
`PortfolioPosition` is a weighted-average query projection; immutable transaction deltas remain
rebuild evidence.

Virtual cash and holdings are fictional internal values, not deposits, customer money, legal
assets/liabilities, custody, brokerage, or execution records. Monetary journals balance per
currency. Non-monetary splits do not fabricate cash entries. Corrections use linked opposite
transactions.

Milestone 4 implements simulated valuation snapshots and descriptive history under ADRs
0010–0013. Tax cost basis, real accounts/orders, settlement, custody, and provenanced FX
conversion remain deferred.
