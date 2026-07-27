# Tenant watchlists

`GET /api/v1/watchlists/effective-permissions` returns tenant-specific booleans derived from the
active server-side membership. The frontend uses them to hide unavailable create, update, delete,
add, remove and reorder controls. API authorisation remains mandatory and authoritative.

Watchlists belong to an Atlas tenant and use UUID identity. Items reference listing UUIDs, never
symbols. A listing appears once; positions are unique, non-negative, and deterministic.

Owners and admins have all permissions. Members may read, create, update, and manage items.
Viewers are read-only. Permissions live in `AuthorisationService`, not route comparisons.

Every lookup verifies the caller's active membership for the watchlist tenant. Guessed IDs,
cross-tenant access, and disallowed mutations conceal existence with `404` where appropriate.
Browser tenant IDs select an object but never grant authority.

Deletion archives. Archived lists reject mutation. Removing an item does not delete catalogue
data. Creation, update, archive, addition, removal, and reorder append identity audit events.
Configurable development defaults are 25 lists per tenant and 100 items per list; these are not
commercial quotas.
