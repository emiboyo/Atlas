import React from "react";
import { createRoot } from "react-dom/client";
import ResearchPage from "@/app/app/research/page";
import { ResearchBrowser } from "@/components/research-browser";
import { ResearchScreen } from "@/components/research-screen";
import "@/app/globals.css";

const strategyId = "11111111-1111-4111-8111-111111111111";
const tenantId = "22222222-2222-4222-8222-222222222222";
const versionId = "33333333-3333-4333-8333-333333333333";
const listingId = "44444444-4444-4444-8444-444444444444";
const runId = "55555555-5555-4555-8555-555555555555";

const strategy = {
  id: strategyId,
  tenant_id: tenantId,
  name: "Browser evidence strategy",
  description: "Bounded historical hypothesis",
  research_purpose: "Independent historical research",
  status: "active",
  current_version_id: versionId,
  version: 2,
  created_at: "2026-07-29T08:00:00Z",
  updated_at: "2026-07-29T09:00:00Z",
};
const version = {
  id: versionId,
  strategy_id: strategyId,
  version_number: 1,
  version_label: "SMA evidence",
  configuration_fingerprint: "abc123",
  base_currency: "GBP",
  benchmark_listing_id: null,
  configuration: { listing_id: listingId },
  created_at: "2026-07-29T08:30:00Z",
};
const run = {
  id: runId,
  tenant_id: tenantId,
  strategy_id: strategyId,
  strategy_version_id: versionId,
  listing_id: listingId,
  status: "completed",
  configuration_fingerprint: "config",
  data_fingerprint: "data",
  start_date: "2025-01-01",
  end_date: "2025-02-01",
  starting_capital: "10000",
  base_currency: "GBP",
  fee_model: "zero_fee",
  fee_value: "0",
  slippage_model: "zero_slippage",
  slippage_bps: "0",
  execution_policy: "next_open",
  sizing_policy: "fixed_percentage_of_available_simulated_cash",
  sizing_value: "100",
  missing_data_policy: "fail_run",
  engine_version: "atlas-deterministic-v1",
  requested_at: "2026-07-29T09:00:00Z",
  completed_at: "2026-07-29T09:00:01Z",
  failure_code: null,
};
const result = {
  run_id: runId,
  starting_value: "10000",
  ending_value: "10100",
  simulated_pnl: "100",
  historical_return: "1",
  event_count: 2,
  completed_trade_count: 1,
  maximum_drawdown: "0.5",
  volatility: "2",
  turnover: "200",
  benchmark_return: "0.8",
  missing_count: 0,
  stale_count: 0,
  unavailable_count: 0,
  excluded_count: 0,
  completeness: "complete",
  result_checksum: "checksum",
};
const permissions = {
  can_read: true,
  can_update: true,
  can_archive: true,
  can_create_version: true,
  can_create_backtest: true,
  can_compare: true,
  can_explain: true,
  can_read_audit: true,
};

function json(value: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

window.fetch = (input: RequestInfo | URL) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  if (url.endsWith("/organisations"))
    return json({ items: [{ id: tenantId, name: "Atlas Lab", role: "owner" }] });
  if (url.includes("/effective-permissions")) return json(permissions);
  if (url.endsWith(`/strategies/${strategyId}`)) return json(strategy);
  if (url.endsWith(`/strategies/${strategyId}/versions`)) return json([version]);
  if (url.includes("/research/strategies?")) return json({ items: [strategy] });
  if (url.includes("/research/backtests?")) return json([run]);
  if (url.endsWith(`/backtests/${runId}`)) return json(run);
  if (url.endsWith(`/backtests/${runId}/result`)) return json(result);
  if (url.endsWith(`/backtests/${runId}/data-quality`)) return json(result);
  if (url.endsWith(`/backtests/${runId}/equity`))
    return json([
      {
        sequence: 1,
        observed_at: "2025-01-01T00:00:00Z",
        total_equity: "10000",
        drawdown_percentage: "0",
      },
    ]);
  if (url.endsWith(`/backtests/${runId}/events`)) return json([]);
  if (url.endsWith(`/backtests/${runId}/explanations`)) return json([]);
  if (url.endsWith(`/backtests/${runId}/audit-events`)) return json([]);
  return json({ code: "not_found", message: "Not found" }, 404);
};

function RoutedResearch() {
  const path = window.location.pathname;
  if (path === "/app/research") return <ResearchPage />;
  if (path === "/app/research/strategies") return <ResearchBrowser />;
  if (path === "/app/research/strategies/new") return <ResearchBrowser creationOnly />;
  if (path === `/app/research/strategies/${strategyId}`)
    return <ResearchScreen view="overview" strategyId={strategyId} />;
  if (path === `/app/research/strategies/${strategyId}/versions/new`)
    return <ResearchScreen view="new-version" strategyId={strategyId} />;
  if (path === "/app/research/backtests") return <ResearchScreen view="runs" />;
  if (path === "/app/research/backtests/new") return <ResearchScreen view="new-run" />;
  if (path === `/app/research/backtests/${runId}`)
    return <ResearchScreen view="run" runId={runId} />;
  if (path === `/app/research/backtests/${runId}/events`)
    return <ResearchScreen view="events" runId={runId} />;
  if (path === `/app/research/backtests/${runId}/analytics`)
    return <ResearchScreen view="analytics" runId={runId} />;
  if (path === `/app/research/backtests/${runId}/explanations`)
    return <ResearchScreen view="explanations" runId={runId} />;
  if (path === `/app/research/backtests/${runId}/audit`)
    return <ResearchScreen view="audit" runId={runId} />;
  if (path === "/app/research/compare") return <ResearchScreen view="compare" />;
  return <h1>Research route not found</h1>;
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <main className="mx-auto min-h-screen max-w-7xl bg-slate-950 px-4 py-10 text-white">
      <RoutedResearch />
    </main>
  </React.StrictMode>,
);
