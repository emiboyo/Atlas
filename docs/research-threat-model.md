# Historical Research Threat Model

## Protected assets

Tenant boundaries, immutable strategy definitions, historical inputs, simulated events, result integrity, audit provenance, credentials, and user trust in the non-advisory boundary.

## Material threats and controls

| Threat                                                      | Control                                                                                   |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Cross-tenant object reference                               | Membership checks, concealed absence, tenant-qualified foreign keys                       |
| Client-forged role, status, result, provider, or provenance | Strict request schemas and server-owned fields                                            |
| Duplicate or conflicting requests                           | Request fingerprints, unique idempotency keys, row locks                                  |
| Look-ahead or nondeterministic replay                       | Ordered observations, explicit execution index, pure Decimal engine, checksums            |
| Evidence mutation or deletion                               | PostgreSQL append-only and completed-run triggers                                         |
| Fabricated or silently converted data                       | Server-resolved simulated provider, explicit currency equality, no interpolation          |
| Explanation causing action                                  | Local descriptive template, separated service, no portfolio or execution connector        |
| Sensitive logs                                              | No tokens, credentials, raw provider payloads, full definitions, prompts, or full outputs |
| Resource abuse                                              | Date/window/list/rule bounds and authenticated tenant permissions                         |

## Residual risk

The small simulated fixture is not representative of real markets; calendar-gap completeness is limited; only one rule is executed; runs are synchronous; benchmark alignment is basic; and the existing temporary dependency exceptions remain. These prevent production approval.
