# Strategy Rule Model

Milestone 5 accepts one versioned rule family: `sma_crossover`, schema version `1`.

Each rule has a stable identifier, a short window from 2 through 100, and a long window from 3 through 250. The short window must be lower than the long window. A version accepts at most ten typed rules, but the initial deterministic runner executes the first rule only; additional rules are retained for forward-compatible research definition and are a documented limitation.

Rules are strict schemas: unknown keys fail validation. The canonical version configuration includes the listing, optional descriptive benchmark, explicit base currency, rule schema, and label. Once created it cannot be changed. A changed hypothesis requires a new version.

AI may explain stored historical results or propose a draft research template outside the execution path. It cannot create, approve, modify, or submit a strategy version or simulated event.
