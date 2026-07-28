from prometheus_client import Counter

PORTFOLIO_REQUESTS = Counter(
    "atlas_portfolio_requests_total",
    "Bounded simulated portfolio API requests.",
    ["operation", "outcome"],
)
PORTFOLIO_CREATIONS = Counter(
    "atlas_portfolio_creations_total",
    "Created simulated portfolios.",
)
SIMULATED_TRANSACTIONS = Counter(
    "atlas_simulated_portfolio_transactions_total",
    "Posted simulated transactions by bounded transaction type.",
    ["transaction_type"],
)
TRANSACTION_CONFLICTS = Counter(
    "atlas_portfolio_transaction_conflicts_total",
    "Simulated transaction conflicts by bounded code.",
    ["code"],
)
IDEMPOTENT_REPLAYS = Counter(
    "atlas_portfolio_idempotent_replays_total",
    "Identical simulated financial mutation replays.",
    ["operation"],
)
REVERSALS = Counter("atlas_portfolio_reversals_total", "Completed simulated reversals.")
VALUATIONS = Counter(
    "atlas_portfolio_valuations_total",
    "Simulated portfolio valuations.",
    ["completeness"],
)
STALE_VALUATIONS = Counter(
    "atlas_portfolio_stale_valuations_total",
    "Simulated portfolio valuations containing stale data.",
)
ANALYTICS_REQUESTS = Counter(
    "atlas_portfolio_analytics_requests_total",
    "Descriptive simulated portfolio analytics requests.",
    ["metric"],
)
INVARIANT_FAILURES = Counter(
    "atlas_portfolio_accounting_invariant_failures_total",
    "Accounting invariant failures by bounded code.",
    ["code"],
)
