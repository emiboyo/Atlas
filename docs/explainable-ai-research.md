# Research Explanation Design

Milestone 5 uses a local deterministic template engine, not an external AI provider. It receives only persisted run and result identifiers, checksum-derived inputs, and an allow-listed explanation type.

Every explanation stores engine, engine version, template version, input fingerprint, output fingerprint, limitations, author, timestamp, and idempotency evidence. Explanations are append-only and may be disabled with `ATLAS_RESEARCH_EXPLANATIONS_ENABLED=false`; the API then returns a safe unavailable state.

Output is descriptive. It cannot claim suitability, causation, certainty, expected future return, recommendation, guarantee, live signal, or execution capability. Complete prompts, model responses, strategy source, tokens, and credentials are not logged.

Only the deterministic backtest engine may generate historical simulated events from an explicitly user-approved immutable configuration. Explanation output cannot create or modify events, strategy versions, portfolios, or financial records.
