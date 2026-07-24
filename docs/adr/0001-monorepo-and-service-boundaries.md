# ADR 0001: Monorepo with explicit deployable boundaries

- Status: Accepted
- Date: 2026-07-24

## Context

Atlas needs fast cross-functional delivery while retaining a path to independent scaling.

## Decision

Use a pnpm/Turborepo monorepo. Next.js and FastAPI are independently deployable applications;
shared code is limited to packages with explicit ownership and contracts. Begin the backend as
a modular monolith and extract services only for proven scaling, reliability, or governance needs.

## Consequences

Atomic changes and consistent tooling remain straightforward. Package boundaries and dependency
direction must be enforced to avoid accidental coupling.
