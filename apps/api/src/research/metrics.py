from prometheus_client import Counter, Histogram

STRATEGY_OPERATIONS = Counter(
    "atlas_research_strategy_operations_total",
    "Bounded research strategy operations.",
    ["operation", "outcome"],
)
BACKTESTS = Counter("atlas_research_backtests_total", "Historical simulation runs.", ["outcome"])
BACKTEST_DURATION = Histogram(
    "atlas_research_backtest_duration_seconds", "Historical simulation duration."
)
RESEARCH_CONFLICTS = Counter("atlas_research_conflicts_total", "Research conflicts.", ["code"])
EXPLANATIONS = Counter(
    "atlas_research_explanations_total", "Local deterministic explanations.", ["outcome"]
)
