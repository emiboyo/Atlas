import Link from "next/link";
import type { Route } from "next";
import { ResearchNotice } from "@/components/research-notice";

type View =
  | "overview"
  | "versions"
  | "new-version"
  | "runs"
  | "new-run"
  | "run"
  | "events"
  | "analytics"
  | "explanations"
  | "audit"
  | "compare";

export function ResearchScreen({
  view,
  strategyId,
  runId,
}: {
  view: View;
  strategyId?: string;
  runId?: string;
}) {
  const titles: Record<View, string> = {
    overview: "Strategy research workspace",
    versions: "Immutable strategy versions",
    "new-version": "Define a strategy version",
    runs: "Historical backtest runs",
    "new-run": "Configure historical simulation",
    run: "Historical run detail",
    events: "Append-only simulated events",
    analytics: "Historical analytics",
    explanations: "Research explanation",
    audit: "Research audit history",
    compare: "Neutral run comparison",
  };
  return (
    <section className="space-y-7">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Private development</p>
        <h1 className="font-display mt-3 text-4xl font-semibold">{titles[view]}</h1>
        <p className="mt-3 max-w-3xl text-slate-400">
          Deterministic, tenant-isolated historical research with explicit assumptions and immutable
          provenance.
        </p>
      </div>
      <ResearchNotice />
      <nav aria-label="Research section" className="flex flex-wrap gap-3 text-sm">
        <Link className="atlas-chip" href="/app/research/strategies">
          Strategies
        </Link>
        <Link className="atlas-chip" href="/app/research/backtests">
          Run history
        </Link>
        <Link className="atlas-chip" href="/app/research/compare">
          Compare
        </Link>
        {strategyId ? (
          <Link
            className="atlas-chip"
            href={`/app/research/strategies/${strategyId}/versions` as Route}
          >
            Versions
          </Link>
        ) : null}
      </nav>
      {view === "new-version" ? <VersionForm strategyId={strategyId ?? ""} /> : null}
      {view === "new-run" ? <BacktestForm /> : null}
      {view === "events" ? <EventTable /> : null}
      {view === "analytics" ? <AnalyticsPanel /> : null}
      {view === "explanations" ? <ExplanationPanel /> : null}
      {view === "audit" ? <AuditPanel /> : null}
      {view === "compare" ? <ComparisonPanel /> : null}
      {![
        "new-version",
        "new-run",
        "events",
        "analytics",
        "explanations",
        "audit",
        "compare",
      ].includes(view) ? (
        <div className="grid gap-4 md:grid-cols-3">
          <article className="atlas-panel p-6">
            <h2 className="font-semibold">Immutable inputs</h2>
            <p className="mt-2 text-sm text-slate-400">
              Configuration, data, engine version, and checksums identify every replay.
            </p>
          </article>
          <article className="atlas-panel p-6">
            <h2 className="font-semibold">Explicit state</h2>
            <p className="mt-2 text-sm text-slate-400">
              Loading, incomplete, stale, missing, unavailable, and failed states remain visible.
            </p>
          </article>
          <article className="atlas-panel p-6">
            <h2 className="font-semibold">No execution path</h2>
            <p className="mt-2 text-sm text-slate-400">
              This workspace has no order, broker, custody, deposit, or withdrawal controls.
            </p>
          </article>
        </div>
      ) : null}
      {runId ? <p className="break-all text-xs text-slate-500">Run reference: {runId}</p> : null}
    </section>
  );
}

function VersionForm({ strategyId }: { strategyId: string }) {
  return (
    <form className="atlas-panel max-w-3xl p-6">
      <fieldset className="grid gap-5">
        <legend className="font-display text-2xl font-semibold">SMA crossover rule</legend>
        <label>
          Version label
          <input className="atlas-input mt-2" required />
        </label>
        <label>
          Listing identifier
          <input className="atlas-input mt-2" required />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            Short window
            <input className="atlas-input mt-2" type="number" min="2" max="100" defaultValue="20" />
          </label>
          <label>
            Long window
            <input className="atlas-input mt-2" type="number" min="3" max="250" defaultValue="50" />
          </label>
        </div>
      </fieldset>
      <p className="mt-4 text-sm text-slate-400">
        The short window must be lower than the long window. Strategy: {strategyId}
      </p>
      <button
        type="button"
        className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
      >
        Save immutable version
      </button>
    </form>
  );
}

function BacktestForm() {
  return (
    <form className="atlas-panel p-6">
      <fieldset className="grid gap-5 md:grid-cols-2">
        <legend className="font-display col-span-full text-2xl font-semibold">
          Explicit simulation assumptions
        </legend>
        <label>
          Start date
          <input className="atlas-input mt-2" type="date" required />
        </label>
        <label>
          End date
          <input className="atlas-input mt-2" type="date" required />
        </label>
        <label>
          Starting virtual capital
          <input className="atlas-input mt-2" inputMode="decimal" defaultValue="10000" />
        </label>
        <label>
          Execution price
          <select className="atlas-input mt-2">
            <option>Next observation open</option>
            <option>Same observation close</option>
            <option>Next observation close</option>
          </select>
        </label>
        <label>
          Fee model
          <select className="atlas-input mt-2">
            <option>Zero fee</option>
            <option>Fixed amount per event</option>
            <option>Percentage of gross value</option>
          </select>
        </label>
        <label>
          Slippage model
          <select className="atlas-input mt-2">
            <option>Zero slippage</option>
            <option>Fixed basis points</option>
          </select>
        </label>
        <label>
          Position sizing
          <select className="atlas-input mt-2">
            <option>Fixed percentage of available simulated cash</option>
            <option>Fixed simulated cash amount</option>
            <option>Fixed quantity</option>
          </select>
        </label>
        <label>
          Missing-data policy
          <select className="atlas-input mt-2">
            <option>Fail run</option>
            <option>Skip event</option>
            <option>Skip observation</option>
          </select>
        </label>
      </fieldset>
      <button
        type="button"
        className="mt-6 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
      >
        Run historical simulation
      </button>
    </form>
  );
}

function EventTable() {
  return (
    <div className="atlas-panel overflow-x-auto p-6">
      <table className="w-full text-left text-sm">
        <caption className="mb-4 text-left text-lg font-semibold">Simulated event sequence</caption>
        <thead>
          <tr>
            <th>Sequence</th>
            <th>Type</th>
            <th>Decision time</th>
            <th>Simulated time</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={5} className="py-6 text-slate-400">
              No simulated events are available for this run.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function AnalyticsPanel() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <article className="atlas-panel p-6">
        <h2 className="font-semibold">Equity and drawdown</h2>
        <p className="mt-3 text-sm text-slate-400">
          Text alternative: equity, peak, and drawdown values are provided chronologically when run
          data loads.
        </p>
      </article>
      <article className="atlas-panel p-6">
        <h2 className="font-semibold">Data quality · unavailable</h2>
        <p className="mt-3 text-sm text-slate-400">
          Missing, stale, unavailable, excluded, and completeness counts are shown without
          interpolation.
        </p>
      </article>
      <article className="atlas-panel p-6 md:col-span-2">
        <h2 className="font-semibold">Descriptive benchmark comparison</h2>
        <p className="mt-3 text-sm text-slate-400">
          Historical percentage changes use the same dates and currency. They are not forecasts or
          recommendations.
        </p>
      </article>
    </div>
  );
}

function ExplanationPanel() {
  return (
    <article className="atlas-panel p-6">
      <h2 className="font-semibold">Optional local explanation</h2>
      <p className="mt-3 text-sm text-slate-400">
        Explanations are disabled safely when configured off. They describe stored historical
        results and cannot create or modify events.
      </p>
      <p className="mt-4 text-sm text-amber-200">
        No advice, suitability assessment, causal claim, guarantee, or future-performance claim is
        generated.
      </p>
    </article>
  );
}

function AuditPanel() {
  return (
    <article className="atlas-panel p-6">
      <h2 className="font-semibold">Append-only evidence</h2>
      <p className="mt-3 text-sm text-slate-400">
        Authorised owners and administrators can inspect strategy, version, run, and explanation
        audit events.
      </p>
    </article>
  );
}

function ComparisonPanel() {
  return (
    <form className="atlas-panel p-6">
      <fieldset>
        <legend className="font-display text-2xl font-semibold">Compare two runs</legend>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label>
            First run identifier
            <input className="atlas-input mt-2" />
          </label>
          <label>
            Second run identifier
            <input className="atlas-input mt-2" />
          </label>
        </div>
      </fieldset>
      <button
        type="button"
        className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
      >
        Compare historical results
      </button>
    </form>
  );
}
