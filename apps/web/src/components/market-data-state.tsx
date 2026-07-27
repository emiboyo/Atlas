type MarketDataStateProps = {
  status: string;
  providerTimestamp?: string;
  delaySeconds?: number | null;
  message?: string;
};

const copy: Record<string, string> = {
  simulated: "Simulated development data",
  delayed: "Delayed market data",
  cached: "Cached market data",
  stale: "Stale market data",
  unavailable: "Market data unavailable",
  provider_error: "Market-data provider unavailable",
  rate_limited: "Market data is temporarily rate limited",
  unsupported_interval: "This historical interval is unsupported",
};

export function MarketDataState({
  status,
  providerTimestamp,
  delaySeconds,
  message,
}: MarketDataStateProps) {
  const label = copy[status] ?? "Market-data status unavailable";
  return (
    <aside
      role="status"
      data-market-status={status}
      className="rounded-2xl border border-amber-300/30 bg-amber-300/10 p-4"
    >
      <strong>{label}</strong>
      {status === "delayed" && delaySeconds != null ? (
        <p className="mt-1 text-sm">Delay: {delaySeconds} seconds.</p>
      ) : null}
      {providerTimestamp ? (
        <p className="mt-1 text-sm">
          Provider timestamp: {new Date(providerTimestamp).toLocaleString()}
        </p>
      ) : null}
      <p className="mt-1 text-sm">
        {message ??
          "Informational data only. Check its source, timestamp and status; this is not investment advice."}
      </p>
    </aside>
  );
}
