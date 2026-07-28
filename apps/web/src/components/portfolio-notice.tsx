export function PortfolioNotice() {
  return (
    <aside
      role="note"
      className="rounded-xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-sm text-amber-100"
    >
      <strong>Simulated portfolio — no real money or orders.</strong>{" "}
      <span className="text-amber-100/80">
        Values are informational, may be stale or unavailable, and are not investment advice.
      </span>
    </aside>
  );
}
