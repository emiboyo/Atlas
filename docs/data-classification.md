# Data classification and handling

## Classification levels

| Level        | Definition                                | Atlas examples                                            | Minimum controls                                                                                |
| ------------ | ----------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Public       | Approved for public release               | Marketing copy, public instrument names                   | Integrity controls, normal backups                                                              |
| Internal     | Non-public operational data               | Feature flags, service metadata                           | Authenticated access, encryption                                                                |
| Confidential | User or commercially sensitive            | Portfolios, holdings, account metadata                    | Tenant isolation, least privilege, audit logging, encryption                                    |
| Restricted   | Highest-impact regulated or security data | Identity verification, tax IDs, bank details, credentials | Field-level protection/tokenization, tightly scoped roles, immutable audit, enhanced monitoring |

## Current schema classification

| Data                                                   | Classification                 | Notes                                                              |
| ------------------------------------------------------ | ------------------------------ | ------------------------------------------------------------------ |
| Instrument and listing reference data                  | Internal/Public after approval | Provider licensing may restrict redistribution                     |
| Tenant and membership mappings                         | Confidential                   | Clerk identifiers are pseudonymous identifiers                     |
| Investment accounts                                    | Confidential                   | External account identifiers require masking in logs and UI        |
| Portfolios and position snapshots                      | Confidential                   | Financial profile and holdings information                         |
| Ledger accounts, transactions, and entries             | Confidential                   | Financial records; immutable retention and reconciliation required |
| Clerk/Stripe keys and JWTs                             | Restricted                     | Secrets only; never persisted in application tables or logs        |
| Atlas user profiles and identity audit events          | Confidential                   | Minimise PII; tenant isolation and append-only audit controls      |
| Clerk webhook identifiers and payload digests          | Confidential                   | Full webhook payloads are not retained                             |
| Future KYC, AML, bank, tax, and government identifiers | Restricted                     | Store only after a dedicated design and regulatory review          |

## Handling requirements

- Encrypt data in transit and at rest with managed KMS keys.
- Prohibit secrets, tokens, full external account identifiers, and holdings from application logs.
- Audit access to Confidential and Restricted records.
- Separate service, migration, analytics, and support database roles.
- Use masked or synthetic data outside production.
- Apply jurisdiction-specific retention, deletion, portability, and legal-hold rules.
- Require reviewed purpose limitation before adding any personal attribute.
- Document provider redistribution and retention rights for every market-data field.

No Restricted customer-identification fields are introduced by the current migration.

Market reference data, fictional fixtures, venue codes, and safe provider labels are Internal.
Watchlist names, descriptions, notes, tenant IDs, and user references are Confidential tenant
data. Provider credentials are Restricted and must never enter observations, logs, API
responses, browser bundles, or Redis. Quote and candle provenance is integrity-sensitive even
when simulated.

## Milestone 4 simulated portfolio data

Simulated portfolios, virtual balances, holdings, paper transactions, valuation snapshots, and
user-entered portfolio notes are Confidential tenant application data. Notes must be bounded and
must not contain real bank, card, payment, tax, passport, brokerage, credential, or customer-fund
data. Simulated balances and transactions must never be represented as customer assets,
liabilities, deposits, withdrawals, or executed orders.

Portfolio audit events are security and financial-integrity records requiring append-only
retention, tenant-aware access, and safe metadata. Provider timestamps, transaction timestamps,
valuation timestamps, receipt timestamps, market-data status, source provenance, and currency
must be retained distinctly. No real bank, card, payment, tax, passport, brokerage, KYC, custody,
or money-movement data is permitted by Milestone 4 governance.

Names, descriptions, transaction reasons, and audit metadata are bounded. They must not contain
credentials, payment data, unrestricted notes, or real customer-fund information. Logs and
metric labels exclude portfolio names, amounts, quantities, user/tenant IDs, holdings, and
complete snapshots. Safe request IDs and bounded operation/result codes are permitted.

Public APIs provide no update/delete operation for transactions, ledger entries, snapshots,
valuation lines, or portfolio audit events; PostgreSQL append-only triggers backstop the policy.
