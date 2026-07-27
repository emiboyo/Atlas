from prometheus_client import Counter, Histogram

MARKET_REQUESTS = Counter(
    "atlas_market_data_requests_total",
    "Bounded market-data API requests.",
    ["operation", "outcome"],
)
PROVIDER_LATENCY = Histogram(
    "atlas_market_provider_latency_seconds",
    "Market-data provider latency.",
    ["provider", "operation"],
)
PROVIDER_ERRORS = Counter(
    "atlas_market_provider_errors_total",
    "Safe provider errors.",
    ["provider", "code"],
)
CACHE_OPERATIONS = Counter(
    "atlas_market_cache_operations_total",
    "Market-data cache operations.",
    ["operation", "result"],
)
STALE_RESPONSES = Counter(
    "atlas_market_stale_responses_total",
    "Explicit stale market-data responses.",
    ["provider"],
)
INGESTION_RESULTS = Counter(
    "atlas_market_ingestion_total",
    "Development ingestion results.",
    ["operation", "outcome"],
)
