# Identity Threat Model

## Protected assets

- authentication integrity and Clerk signing configuration;
- Atlas user and profile records;
- tenant membership, ownership, and platform roles;
- identity audit history;
- confidential profile and workspace metadata.

## Principal threats and controls

| Threat                                  | Control                                                                       |
| --------------------------------------- | ----------------------------------------------------------------------------- |
| Forged or modified JWT                  | RS256 allowlist, JWKS signature verification, issuer/audience/time validation |
| Algorithm confusion                     | PyJWT receives only `RS256`; unverified payloads are never trusted            |
| Unknown or rotated key                  | Bounded JWKS cache and refresh; unknown keys fail closed                      |
| Clerk/JWKS outage                       | Stable `503`; no development bypass                                           |
| IDOR by organisation ID                 | Local active-membership lookup; unrelated objects concealed as `404`          |
| Client role or platform-role escalation | Extra fields forbidden; local server-side role matrix                         |
| Final-owner race                        | Transactional service plus tenant-scoped PostgreSQL lock/trigger              |
| Webhook forgery or replay               | Raw-body Svix HMAC verification, timestamp tolerance, unique inbox ID         |
| Oversized webhook                       | Content-Length and actual-body byte limits                                    |
| Out-of-order deletion                   | Deactivated tombstone; later create does not reactivate automatically         |
| Audit tampering                         | No mutation API and PostgreSQL update/delete trigger                          |
| Token leakage                           | No token persistence or logging; browser uses Clerk token acquisition         |
| Open redirect                           | Protected layout uses a fixed internal redirect                               |
| Mass assignment                         | Pydantic `extra="forbid"` and explicit field application                      |
| XSS through names                       | React escaped rendering and existing CSP                                      |

## Residual and deferred risk

Production provider configuration, key-rotation exercises, application-level rate limiting,
session revocation integration, consent-version records, privacy erasure, support/compliance
administration, and KYC are deferred. Production and public access remain prohibited under the
Milestone 1 governance decisions.
