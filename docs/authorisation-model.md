# Authorisation Model

Watchlist effective permissions are derived from the active tenant membership on the server and
returned as bounded booleans for UI rendering. They cannot be supplied or overridden by the
browser and never replace API-side permission enforcement.

## Principles

- Authentication proves the external identity; local Atlas state authorises resources.
- Every organisation object is loaded through an active local membership.
- Cross-tenant misses return `404` where existence should be concealed.
- Platform roles are separate from organisation roles and are not publicly editable.
- Role comparisons are centralised in `AuthorisationService`.
- Database constraints and triggers backstop service rules.

## Permission matrix

| Permission             | Owner | Admin | Member | Viewer |
| ---------------------- | :---: | :---: | :----: | :----: |
| `organisation:read`    |  Yes  |  Yes  |  Yes   |  Yes   |
| `organisation:update`  |  Yes  |  Yes  |   No   |   No   |
| `membership:read`      |  Yes  |  Yes  |  Yes   |   No   |
| `membership:invite`    |  Yes  |  Yes  |   No   |   No   |
| `membership:update`    |  Yes  |  Yes  |   No   |   No   |
| `membership:remove`    |  Yes  |  Yes  |   No   |   No   |
| `profile:read:self`    |  Yes  |  Yes  |  Yes   |  Yes   |
| `profile:update:self`  |  Yes  |  Yes  |  Yes   |  Yes   |
| `audit:read`           |  Yes  |  Yes  |   No   |   No   |
| `ownership:transfer`   |  Yes  |  No   |   No   |   No   |
| `organisation:archive` |  Yes  |  No   |   No   |   No   |

Admins cannot assign or remove ownership. Ownership transfer is an owner-only transactional
operation. PostgreSQL takes a tenant-scoped advisory transaction lock and rejects removal,
demotion, or suspension of the final active owner. This protects against concurrent requests as
well as ordinary service mistakes.

## Status enforcement

Only active Atlas users receive normal protected access. Suspended and deactivated users receive
`403 account_inactive`. Only active memberships count for access. Suspended, removed, or invited
memberships do not grant access. Suspended, archived, or closed workspaces reject ordinary
mutations.

## Error semantics

- `401`: bearer token is missing, malformed, expired, invalid, or signed by an unknown key.
- `403`: identity is valid but the Atlas user is inactive or lacks permission.
- `404`: a tenant-scoped object is absent or belongs to another tenant.
- `409`: lifecycle, uniqueness, final-owner, or state-transition conflict.

Every API response carries a request ID through the shared middleware and stable error envelope.

## Watchlist permissions

`watchlist:read`, `watchlist:create`, `watchlist:update`, `watchlist:delete`,
`watchlist:item:add`, and `watchlist:item:remove` use the same central matrix. Owners and admins
receive all six. Members receive read, create, update, add, and remove. Viewers receive read only.
Browser-selected tenant and watchlist IDs never establish authority; PostgreSQL membership is
resolved for every operation.
