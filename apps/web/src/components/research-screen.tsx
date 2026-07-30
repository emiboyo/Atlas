"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ResearchNotice } from "@/components/research-notice";
import { AtlasApiError, atlasApi } from "@/lib/api-client";

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
type Organisation = { id: string; name: string };
type Permissions = {
  can_read: boolean;
  can_update: boolean;
  can_archive: boolean;
  can_create_version: boolean;
  can_create_backtest: boolean;
  can_compare: boolean;
  can_explain: boolean;
  can_read_audit: boolean;
};
const deniedPermissions: Permissions = {
  can_read: false,
  can_update: false,
  can_archive: false,
  can_create_version: false,
  can_create_backtest: false,
  can_compare: false,
  can_explain: false,
  can_read_audit: false,
};

function normalizePermissions(value: unknown): Permissions {
  if (!value || typeof value !== "object") return deniedPermissions;
  const candidate = value as Record<keyof Permissions, unknown>;
  const keys = Object.keys(deniedPermissions) as (keyof Permissions)[];
  if (keys.some((key) => typeof candidate[key] !== "boolean")) return deniedPermissions;
  return Object.fromEntries(keys.map((key) => [key, candidate[key]])) as Permissions;
}
type Strategy = {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  research_purpose: string;
  status: string;
  current_version_id: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};
type Version = {
  id: string;
  strategy_id: string;
  version_number: number;
  version_label: string;
  configuration_fingerprint: string;
  base_currency: string;
  benchmark_listing_id: string | null;
  configuration: { listing_id?: string };
  created_at: string;
};
type Run = {
  id: string;
  tenant_id: string;
  strategy_id: string;
  strategy_version_id: string;
  listing_id: string;
  status: string;
  configuration_fingerprint: string;
  data_fingerprint: string | null;
  start_date: string;
  end_date: string;
  starting_capital: string;
  base_currency: string;
  fee_model: string;
  fee_value: string;
  slippage_model: string;
  slippage_bps: string;
  execution_policy: string;
  sizing_policy: string;
  sizing_value: string;
  missing_data_policy: string;
  engine_version: string;
  requested_at: string;
  completed_at: string | null;
  failure_code: string | null;
};
type Event = {
  id: string;
  sequence: number;
  listing_id: string;
  event_type: string;
  decision_at: string;
  simulated_at: string;
  price: string;
  quantity: string;
  fee: string;
  slippage: string;
  cash_before: string;
  cash_after: string;
  position_before: string;
  position_after: string;
  triggered_rule_ids: string[];
};
type Equity = {
  sequence: number;
  observed_at: string;
  total_equity: string;
  drawdown_percentage: string;
};
type Result = {
  run_id: string;
  starting_value: string;
  ending_value: string;
  simulated_pnl: string;
  historical_return: string;
  event_count: number;
  completed_trade_count: number;
  maximum_drawdown: string;
  volatility: string | null;
  turnover: string;
  benchmark_return: string | null;
  missing_count: number;
  stale_count: number;
  unavailable_count: number;
  excluded_count: number;
  completeness: string;
  result_checksum: string;
};
type Explanation = {
  id: string;
  explanation_type: string;
  engine_identifier: string;
  engine_version: string;
  template_version: string;
  explanation_text: string;
  limitations: string;
  status: string;
  generated_at: string;
};
type Audit = {
  id: string;
  event_type: string;
  actor_user_id: string;
  target_id: string | null;
  created_at: string;
};

const titles: Record<View, string> = {
  overview: "Strategy detail",
  versions: "Immutable strategy versions",
  "new-version": "Define a strategy version",
  runs: "Historical backtest runs",
  "new-run": "Configure historical simulation",
  run: "Historical run detail",
  events: "Append-only simulated events",
  analytics: "Historical analytics",
  explanations: "Research explanations",
  audit: "Research audit history",
  compare: "Neutral run comparison",
};

function messageFor(error: unknown) {
  if (error instanceof AtlasApiError) {
    if (error.status === 401) return "Your session has expired. Sign in again.";
    if (error.status === 403) return "You do not have permission to view this resource.";
    if (error.status === 404) return "This research resource was not found.";
    return `${error.message}${error.requestId ? ` Reference: ${error.requestId}` : ""}`;
  }
  return error instanceof Error ? error.message : "The research service is unavailable.";
}

function idempotencyKey() {
  return globalThis.crypto?.randomUUID() ?? `atlas-${Date.now()}-research`;
}

export function ResearchScreen(props: { view: View; strategyId?: string; runId?: string }) {
  return (
    <section className="space-y-7">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Private development</p>
        <h1 className="font-display mt-3 text-4xl font-semibold">{titles[props.view]}</h1>
        <p className="mt-3 max-w-3xl text-slate-400">
          Deterministic, tenant-isolated historical research with explicit assumptions and immutable
          provenance.
        </p>
      </div>
      <ResearchNotice />
      <ResearchNavigation strategyId={props.strategyId} runId={props.runId} />
      <ResearchData {...props} />
    </section>
  );
}

function ResearchNavigation({ strategyId, runId }: { strategyId?: string; runId?: string }) {
  return (
    <nav aria-label="Research section" className="flex flex-wrap gap-3 text-sm">
      <Link className="atlas-chip" href="/app/research">
        Research home
      </Link>
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
      {runId ? (
        <>
          <Link className="atlas-chip" href={`/app/research/backtests/${runId}` as Route}>
            Run
          </Link>
          <Link className="atlas-chip" href={`/app/research/backtests/${runId}/events` as Route}>
            Events
          </Link>
          <Link className="atlas-chip" href={`/app/research/backtests/${runId}/analytics` as Route}>
            Analytics
          </Link>
          <Link
            className="atlas-chip"
            href={`/app/research/backtests/${runId}/explanations` as Route}
          >
            Explanations
          </Link>
          <Link className="atlas-chip" href={`/app/research/backtests/${runId}/audit` as Route}>
            Audit
          </Link>
        </>
      ) : null}
    </nav>
  );
}

function ResearchData({
  view,
  strategyId,
  runId,
}: {
  view: View;
  strategyId?: string;
  runId?: string;
}) {
  const { getToken } = useAuth();
  const [data, setData] = useState<unknown>(null);
  const [permissions, setPermissions] = useState<Permissions | null>(null);
  const [message, setMessage] = useState("Loading historical research data…");
  const [busy, setBusy] = useState(false);

  async function token() {
    const value = await getToken();
    if (!value) throw new AtlasApiError("Authentication is required.", 401, "unauthenticated");
    return value;
  }

  async function organisations() {
    return atlasApi<{ items: Organisation[] }>("/organisations", await token());
  }

  async function load() {
    setMessage("Loading historical research data…");
    try {
      const auth = await token();
      if (view === "overview" && strategyId) {
        const [strategy, allowed] = await Promise.all([
          atlasApi<Strategy>(`/research/strategies/${strategyId}`, auth),
          atlasApi<Permissions>(`/research/strategies/${strategyId}/effective-permissions`, auth),
        ]);
        setData(strategy);
        setPermissions(normalizePermissions(allowed));
      } else if ((view === "versions" || view === "new-version") && strategyId) {
        const [strategy, versions, allowed] = await Promise.all([
          atlasApi<Strategy>(`/research/strategies/${strategyId}`, auth),
          atlasApi<Version[]>(`/research/strategies/${strategyId}/versions`, auth),
          atlasApi<Permissions>(`/research/strategies/${strategyId}/effective-permissions`, auth),
        ]);
        setData({ strategy, versions });
        setPermissions(normalizePermissions(allowed));
      } else if (view === "runs" || view === "new-run" || view === "compare") {
        const orgs = await organisations();
        const tenant = orgs.items[0];
        if (!tenant) {
          setData({ tenant: null, strategies: [], runs: [] });
          setMessage("Choose or create an authorised organisation before using research.");
          return;
        }
        const [strategyPage, runs] = await Promise.all([
          atlasApi<{ items: Strategy[] }>(
            `/research/strategies?tenant_id=${encodeURIComponent(tenant.id)}`,
            auth,
          ),
          atlasApi<Run[]>(`/research/backtests?tenant_id=${encodeURIComponent(tenant.id)}`, auth),
        ]);
        setData({ tenant, strategies: strategyPage.items, runs });
      } else if (runId) {
        const run = await atlasApi<Run>(`/research/backtests/${runId}`, auth);
        const allowed = await atlasApi<Permissions>(
          `/research/strategies/${run.strategy_id}/effective-permissions`,
          auth,
        );
        setPermissions(normalizePermissions(allowed));
        if (view === "run") {
          const result =
            run.status === "completed"
              ? await atlasApi<Result>(`/research/backtests/${runId}/result`, auth)
              : null;
          setData({ run, result });
        } else if (view === "events") {
          setData(await atlasApi<Event[]>(`/research/backtests/${runId}/events`, auth));
        } else if (view === "analytics") {
          const [result, equity, quality] = await Promise.all([
            atlasApi<Result>(`/research/backtests/${runId}/result`, auth),
            atlasApi<Equity[]>(`/research/backtests/${runId}/equity`, auth),
            atlasApi<Result>(`/research/backtests/${runId}/data-quality`, auth),
          ]);
          setData({ result, equity, quality });
        } else if (view === "explanations") {
          setData(await atlasApi<Explanation[]>(`/research/backtests/${runId}/explanations`, auth));
        } else if (view === "audit") {
          setData(await atlasApi<Audit[]>(`/research/backtests/${runId}/audit-events`, auth));
        }
      }
      setMessage("");
    } catch (error) {
      setData(null);
      setMessage(messageFor(error));
    }
  }

  useEffect(() => {
    // The effect synchronises the authenticated route with its API resource.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
    // Route identifiers and active Clerk context determine the resource.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, strategyId, runId]);

  function announce(value: string) {
    setMessage(value);
    requestAnimationFrame(() =>
      document.querySelector<HTMLElement>('[data-research-status="true"]')?.focus(),
    );
  }

  async function mutate(action: (auth: string) => Promise<void>) {
    if (busy) return;
    setBusy(true);
    try {
      await action(await token());
      await load();
    } catch (error) {
      announce(messageFor(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <p
        data-research-status="true"
        role="status"
        aria-live="polite"
        tabIndex={-1}
        className="text-sm text-amber-100"
      >
        {message}
      </p>
      {data ? renderView(view, data, permissions, busy, mutate, announce, runId) : null}
    </div>
  );
}

type Mutate = (action: (auth: string) => Promise<void>) => Promise<void>;
function renderView(
  view: View,
  data: unknown,
  permissions: Permissions | null,
  busy: boolean,
  mutate: Mutate,
  announce: (value: string) => void,
  runId?: string,
): ReactNode {
  if (view === "overview")
    return (
      <StrategyDetail
        strategy={data as Strategy}
        permissions={permissions}
        busy={busy}
        mutate={mutate}
      />
    );
  if (view === "versions")
    return (
      <VersionHistory
        data={data as { strategy: Strategy; versions: Version[] }}
        permissions={permissions}
      />
    );
  if (view === "new-version")
    return (
      <VersionForm
        data={data as { strategy: Strategy; versions: Version[] }}
        permissions={permissions}
        busy={busy}
        mutate={mutate}
        announce={announce}
      />
    );
  if (view === "runs")
    return <RunHistory data={data as { tenant: Organisation | null; runs: Run[] }} />;
  if (view === "new-run")
    return (
      <BacktestForm
        data={data as { tenant: Organisation | null; strategies: Strategy[]; runs: Run[] }}
        busy={busy}
        mutate={mutate}
        announce={announce}
      />
    );
  if (view === "run") return <RunDetail data={data as { run: Run; result: Result | null }} />;
  if (view === "events") return <EventTable events={data as Event[]} />;
  if (view === "analytics")
    return <AnalyticsPanel data={data as { result: Result; equity: Equity[]; quality: Result }} />;
  if (view === "explanations")
    return (
      <ExplanationPanel
        explanations={data as Explanation[]}
        runId={runId ?? ""}
        permissions={permissions}
        busy={busy}
        mutate={mutate}
      />
    );
  if (view === "audit") return <AuditPanel events={data as Audit[]} permissions={permissions} />;
  return (
    <ComparisonPanel
      data={data as { tenant: Organisation | null; runs: Run[] }}
      busy={busy}
      mutate={mutate}
      announce={announce}
    />
  );
}

function StrategyDetail({
  strategy,
  permissions,
  busy,
  mutate,
}: {
  strategy: Strategy;
  permissions: Permissions | null;
  busy: boolean;
  mutate: Mutate;
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
      <article className="atlas-panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-2xl font-semibold">{strategy.name}</h2>
          <span className="atlas-chip">{strategy.status}</span>
        </div>
        <p className="mt-4 text-slate-300">{strategy.description || "No description supplied."}</p>
        <p className="mt-3 text-sm text-slate-400">{strategy.research_purpose}</p>
        <dl className="mt-6 grid gap-3 text-sm sm:grid-cols-2">
          <Meta label="Created" value={new Date(strategy.created_at).toLocaleString()} />
          <Meta label="Updated" value={new Date(strategy.updated_at).toLocaleString()} />
          <Meta label="Revision" value={String(strategy.version)} />
          <Meta
            label="Current version"
            value={strategy.current_version_id ?? "No published version"}
          />
        </dl>
      </article>
      <div className="space-y-3">
        {permissions?.can_create_version && strategy.status !== "archived" ? (
          <Link
            className="block rounded-xl bg-cyan-300 px-4 py-3 text-center font-semibold text-slate-950"
            href={`/app/research/strategies/${strategy.id}/versions/new` as Route}
          >
            Create immutable version
          </Link>
        ) : null}
        {permissions?.can_update && strategy.status !== "archived" ? (
          <StrategyUpdateForm strategy={strategy} busy={busy} mutate={mutate} />
        ) : null}
        {permissions?.can_archive && strategy.status !== "archived" ? (
          <button
            disabled={busy}
            className="w-full rounded-xl border border-amber-300/40 px-4 py-3"
            onClick={() => {
              if (window.confirm("Archive this strategy? New versions and runs will be blocked."))
                void mutate(async (auth) => {
                  await atlasApi(`/research/strategies/${strategy.id}/archive`, auth, {
                    method: "POST",
                  });
                });
            }}
          >
            Archive strategy
          </button>
        ) : null}
      </div>
    </div>
  );
}

function StrategyUpdateForm({
  strategy,
  busy,
  mutate,
}: {
  strategy: Strategy;
  busy: boolean;
  mutate: Mutate;
}) {
  return (
    <form
      className="atlas-panel p-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        void mutate(async (auth) => {
          await atlasApi(`/research/strategies/${strategy.id}`, auth, {
            method: "PATCH",
            body: JSON.stringify({
              name: form.get("name"),
              description: form.get("description") || null,
              research_purpose: form.get("purpose"),
              version: strategy.version,
            }),
          });
        });
      }}
    >
      <h3 className="font-semibold">Update strategy</h3>
      <label className="mt-3 block text-sm">
        Name
        <input
          name="name"
          className="atlas-input mt-1"
          defaultValue={strategy.name}
          maxLength={160}
          required
        />
      </label>
      <label className="mt-3 block text-sm">
        Description
        <textarea
          name="description"
          className="atlas-input mt-1"
          defaultValue={strategy.description ?? ""}
          maxLength={1000}
        />
      </label>
      <label className="mt-3 block text-sm">
        Purpose
        <textarea
          name="purpose"
          className="atlas-input mt-1"
          defaultValue={strategy.research_purpose}
          maxLength={500}
          required
        />
      </label>
      <button
        disabled={busy}
        className="mt-3 rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
      >
        {busy ? "Saving…" : "Save changes"}
      </button>
    </form>
  );
}

function VersionHistory({
  data,
  permissions,
}: {
  data: { strategy: Strategy; versions: Version[] };
  permissions: Permissions | null;
}) {
  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">{data.strategy.name}</h2>
        {permissions?.can_create_version && data.strategy.status !== "archived" ? (
          <Link
            className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
            href={`/app/research/strategies/${data.strategy.id}/versions/new` as Route}
          >
            New version
          </Link>
        ) : null}
      </div>
      {data.versions.length ? (
        <div className="mt-4 grid gap-4">
          {data.versions.map((version) => (
            <article className="atlas-panel p-5" key={version.id}>
              <h3 className="font-semibold">
                Version {version.version_number}: {version.version_label}
              </h3>
              <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                <Meta label="Currency" value={version.base_currency} />
                <Meta label="Created" value={new Date(version.created_at).toLocaleString()} />
                <Meta label="Fingerprint" value={version.configuration_fingerprint} />
                <Meta label="Benchmark" value={version.benchmark_listing_id ?? "None"} />
              </dl>
              <p className="mt-3 text-xs text-slate-400">Immutable version ID: {version.id}</p>
            </article>
          ))}
        </div>
      ) : (
        <Empty>No immutable versions exist for this strategy.</Empty>
      )}
    </section>
  );
}

function VersionForm({
  data,
  permissions,
  busy,
  mutate,
  announce,
}: {
  data: { strategy: Strategy };
  permissions: Permissions | null;
  busy: boolean;
  mutate: Mutate;
  announce: (value: string) => void;
}) {
  if (!permissions?.can_create_version)
    return <Empty>You do not have permission to create strategy versions.</Empty>;
  return (
    <form
      className="atlas-panel max-w-3xl p-6"
      onSubmit={(event) => {
        event.preventDefault();
        const f = new FormData(event.currentTarget);
        const shortWindow = Number(f.get("short"));
        const longWindow = Number(f.get("long"));
        if (shortWindow >= longWindow) {
          announce("Validation error: short window must be less than long window.");
          return;
        }
        void mutate(async (auth) => {
          const version = await atlasApi<Version>(
            `/research/strategies/${data.strategy.id}/versions`,
            auth,
            {
              method: "POST",
              headers: { "Idempotency-Key": idempotencyKey() },
              body: JSON.stringify({
                version_label: f.get("label"),
                base_currency: f.get("currency"),
                listing_id: f.get("listing"),
                benchmark_listing_id: f.get("benchmark") || null,
                rules: [
                  {
                    id: "primary_sma",
                    rule_type: "sma_crossover",
                    schema_version: 1,
                    short_window: shortWindow,
                    long_window: longWindow,
                  },
                ],
              }),
            },
          );
          window.location.assign(
            `/app/research/strategies/${data.strategy.id}/versions#${version.id}`,
          );
        });
      }}
    >
      <fieldset className="grid gap-4">
        <legend className="font-display text-2xl font-semibold">Typed SMA crossover rule</legend>
        <label>
          Version label
          <input name="label" className="atlas-input mt-2" maxLength={80} required />
        </label>
        <label>
          Atlas listing UUID
          <input name="listing" className="atlas-input mt-2" required />
        </label>
        <label>
          Optional benchmark listing UUID
          <input name="benchmark" className="atlas-input mt-2" />
        </label>
        <label>
          Base currency
          <input
            name="currency"
            className="atlas-input mt-2"
            defaultValue="GBP"
            pattern="[A-Z]{3}"
            required
          />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            Short window
            <input
              name="short"
              className="atlas-input mt-2"
              type="number"
              min={2}
              max={100}
              defaultValue={20}
              required
            />
          </label>
          <label>
            Long window
            <input
              name="long"
              className="atlas-input mt-2"
              type="number"
              min={3}
              max={250}
              defaultValue={50}
              required
            />
          </label>
        </div>
      </fieldset>
      <p className="mt-4 text-sm text-slate-400">
        Execution, fees, slippage, sizing, and starting capital are explicit immutable run
        assumptions configured when a backtest is created.
      </p>
      <button
        disabled={busy}
        className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
      >
        {busy ? "Saving…" : "Save immutable version"}
      </button>
    </form>
  );
}

function RunHistory({ data }: { data: { tenant: Organisation | null; runs: Run[] } }) {
  if (!data.tenant) return null;
  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-400">Workspace: {data.tenant.name}</p>
        <Link
          className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
          href="/app/research/backtests/new"
        >
          New historical run
        </Link>
      </div>
      {data.runs.length ? (
        <div className="mt-4 grid gap-4">
          {data.runs.map((run) => (
            <Link
              className="atlas-panel p-5"
              href={`/app/research/backtests/${run.id}` as Route}
              key={run.id}
            >
              <div className="flex justify-between gap-3">
                <strong>
                  {run.start_date} to {run.end_date}
                </strong>
                <span className="atlas-chip">{run.status}</span>
              </div>
              <p className="mt-2 text-sm text-slate-400">
                Strategy version {run.strategy_version_id} · requested{" "}
                {new Date(run.requested_at).toLocaleString()}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <Empty>No historical backtest runs exist in this workspace.</Empty>
      )}
    </section>
  );
}

function BacktestForm({
  data,
  busy,
  mutate,
  announce,
}: {
  data: { tenant: Organisation | null; strategies: Strategy[] };
  busy: boolean;
  mutate: Mutate;
  announce: (value: string) => void;
}) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [canCreate, setCanCreate] = useState(false);
  const { getToken } = useAuth();
  if (!data.tenant) return null;
  return (
    <form
      className="atlas-panel p-6"
      onSubmit={(event) => {
        event.preventDefault();
        const f = new FormData(event.currentTarget);
        if (!f.get("version")) {
          announce("Validation error: select an immutable strategy version.");
          return;
        }
        void mutate(async (auth) => {
          const run = await atlasApi<Run>("/research/backtests", auth, {
            method: "POST",
            headers: { "Idempotency-Key": idempotencyKey() },
            body: JSON.stringify({
              strategy_id: f.get("strategy"),
              strategy_version_id: f.get("version"),
              start_date: f.get("start"),
              end_date: f.get("end"),
              starting_capital: f.get("capital"),
              fee_model: f.get("feeModel"),
              fee_value: f.get("fee"),
              slippage_model: f.get("slippageModel"),
              slippage_bps: f.get("slippage"),
              execution_policy: f.get("execution"),
              sizing_policy: f.get("sizingPolicy"),
              sizing_value: f.get("sizing"),
              missing_data_policy: "fail_run",
            }),
          });
          window.location.assign(`/app/research/backtests/${run.id}`);
        });
      }}
    >
      <fieldset className="grid gap-5 md:grid-cols-2">
        <legend className="font-display col-span-full text-2xl font-semibold">
          Explicit simulation assumptions
        </legend>
        <label className="md:col-span-2">
          Strategy
          <select
            name="strategy"
            className="atlas-input mt-2"
            required
            defaultValue=""
            onChange={(event) => {
              const selected = event.target.value;
              setVersions([]);
              setCanCreate(false);
              if (!selected) return;
              void (async () => {
                try {
                  const auth = await getToken();
                  if (!auth) throw new Error("Authentication is required.");
                  const [availableVersions, effective] = await Promise.all([
                    atlasApi<Version[]>(`/research/strategies/${selected}/versions`, auth),
                    atlasApi<unknown>(
                      `/research/strategies/${selected}/effective-permissions`,
                      auth,
                    ),
                  ]);
                  setVersions(availableVersions);
                  setCanCreate(normalizePermissions(effective).can_create_backtest);
                } catch (error) {
                  announce(messageFor(error));
                }
              })();
            }}
          >
            <option value="" disabled>
              Select strategy
            </option>
            {data.strategies
              .filter((s) => s.status !== "archived")
              .map((s) => (
                <option value={s.id} key={s.id}>
                  {s.name}
                </option>
              ))}
          </select>
        </label>
        <label className="md:col-span-2">
          Immutable version
          <select name="version" className="atlas-input mt-2" required defaultValue="">
            <option value="" disabled>
              Select version
            </option>
            {versions.map((v) => (
              <option value={v.id} key={v.id}>
                Version {v.version_number}: {v.version_label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Start date
          <input name="start" className="atlas-input mt-2" type="date" required />
        </label>
        <label>
          End date
          <input name="end" className="atlas-input mt-2" type="date" required />
        </label>
        <label>
          Starting simulated capital
          <input
            name="capital"
            className="atlas-input mt-2"
            inputMode="decimal"
            defaultValue="10000"
            required
          />
        </label>
        <label>
          Execution assumption
          <select name="execution" className="atlas-input mt-2">
            <option value="next_open">Next observation open</option>
            <option value="same_close">Same observation close</option>
            <option value="next_close">Next observation close</option>
          </select>
        </label>
        <label>
          Fee model
          <select name="feeModel" className="atlas-input mt-2">
            <option value="zero_fee">Zero fee</option>
            <option value="fixed_amount_per_event">Fixed amount per event</option>
            <option value="percentage_of_gross_value">Percentage of gross value</option>
          </select>
        </label>
        <label>
          Fee value
          <input name="fee" className="atlas-input mt-2" inputMode="decimal" defaultValue="0" />
        </label>
        <label>
          Slippage model
          <select name="slippageModel" className="atlas-input mt-2">
            <option value="zero_slippage">Zero slippage</option>
            <option value="fixed_basis_points">Fixed basis points</option>
          </select>
        </label>
        <label>
          Slippage basis points
          <input
            name="slippage"
            className="atlas-input mt-2"
            inputMode="decimal"
            defaultValue="0"
          />
        </label>
        <label>
          Position sizing
          <select name="sizingPolicy" className="atlas-input mt-2">
            <option value="fixed_percentage_of_available_simulated_cash">
              Percentage of available simulated cash
            </option>
            <option value="fixed_simulated_cash_amount">Fixed simulated cash</option>
            <option value="fixed_quantity">Fixed quantity</option>
          </select>
        </label>
        <label>
          Sizing value
          <input
            name="sizing"
            className="atlas-input mt-2"
            inputMode="decimal"
            defaultValue="100"
            required
          />
        </label>
        <label>
          Missing-data policy
          <select className="atlas-input mt-2" disabled>
            <option>Fail run (only supported policy)</option>
          </select>
        </label>
      </fieldset>
      <button
        disabled={busy || !data.strategies.length || !canCreate}
        className="mt-6 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
      >
        {busy ? "Submitting…" : "Run historical simulation"}
      </button>
    </form>
  );
}

function RunDetail({ data }: { data: { run: Run; result: Result | null } }) {
  const { run, result } = data;
  return (
    <div className="space-y-5">
      <article className="atlas-panel p-6">
        <div className="flex justify-between gap-3">
          <h2 className="font-display text-2xl font-semibold">Run {run.id}</h2>
          <span className="atlas-chip">{run.status}</span>
        </div>
        <dl className="mt-5 grid gap-3 sm:grid-cols-2">
          <Meta label="Historical period" value={`${run.start_date} to ${run.end_date}`} />
          <Meta label="Starting capital" value={`${run.starting_capital} ${run.base_currency}`} />
          <Meta label="Execution" value={run.execution_policy} />
          <Meta label="Fee" value={`${run.fee_model}: ${run.fee_value}`} />
          <Meta label="Slippage" value={`${run.slippage_model}: ${run.slippage_bps} bps`} />
          <Meta label="Sizing" value={`${run.sizing_policy}: ${run.sizing_value}`} />
          <Meta label="Missing data" value={run.missing_data_policy} />
          <Meta label="Engine" value={run.engine_version} />
          <Meta label="Configuration fingerprint" value={run.configuration_fingerprint} />
          <Meta label="Data fingerprint" value={run.data_fingerprint ?? "Pending"} />
        </dl>
        {run.failure_code ? (
          <p className="mt-4 text-red-300">Failed safely: {run.failure_code}</p>
        ) : null}
      </article>
      {result ? (
        <ResultSummary result={result} />
      ) : (
        <Empty>No completed result is available for this run.</Empty>
      )}
    </div>
  );
}

function EventTable({ events }: { events: Event[] }) {
  return (
    <div className="atlas-panel overflow-x-auto p-6">
      <table className="w-full text-left text-sm">
        <caption className="mb-4 text-left text-lg font-semibold">
          Historical simulated event sequence
        </caption>
        <thead>
          <tr>
            <th>Seq.</th>
            <th>Type</th>
            <th>Decision</th>
            <th>Simulated execution</th>
            <th>Listing</th>
            <th>Price / quantity</th>
            <th>Fees / slippage</th>
            <th>Cash before / after</th>
            <th>Position before / after</th>
            <th>Rules</th>
          </tr>
        </thead>
        <tbody>
          {events.length ? (
            events.map((event) => (
              <tr className="border-t border-white/10" key={event.id}>
                <td>{event.sequence}</td>
                <td>{event.event_type} (simulated)</td>
                <td>{new Date(event.decision_at).toLocaleString()}</td>
                <td>{new Date(event.simulated_at).toLocaleString()}</td>
                <td>{event.listing_id}</td>
                <td>
                  {event.price} / {event.quantity}
                </td>
                <td>
                  {event.fee} / {event.slippage}
                </td>
                <td>
                  {event.cash_before} / {event.cash_after}
                </td>
                <td>
                  {event.position_before} / {event.position_after}
                </td>
                <td>{event.triggered_rule_ids.join(", ")}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={10} className="py-6 text-slate-400">
                No simulated events occurred.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function AnalyticsPanel({ data }: { data: { result: Result; equity: Equity[]; quality: Result } }) {
  return (
    <div className="space-y-5">
      <ResultSummary result={data.result} />
      <div className="atlas-panel overflow-x-auto p-6">
        <table className="w-full text-left text-sm">
          <caption className="mb-3 text-left font-semibold">
            Accessible equity and drawdown history
          </caption>
          <thead>
            <tr>
              <th>Sequence</th>
              <th>Observed</th>
              <th>Total simulated equity</th>
              <th>Drawdown %</th>
            </tr>
          </thead>
          <tbody>
            {data.equity.map((point) => (
              <tr key={point.sequence}>
                <td>{point.sequence}</td>
                <td>{new Date(point.observed_at).toLocaleString()}</td>
                <td>{point.total_equity}</td>
                <td>{point.drawdown_percentage}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <article className="atlas-panel p-6">
        <h2 className="font-semibold">Data quality and limitations</h2>
        <p className="mt-2">
          Completeness: {data.quality.completeness}. Missing {data.quality.missing_count}; stale{" "}
          {data.quality.stale_count}; unavailable {data.quality.unavailable_count}; excluded{" "}
          {data.quality.excluded_count}.
        </p>
        <p className="mt-2 text-sm text-slate-400">
          No interpolation, prediction, recommendation, or future-performance claim is made.
        </p>
      </article>
    </div>
  );
}

function ResultSummary({ result }: { result: Result }) {
  return (
    <article className="atlas-panel p-6">
      <h2 className="font-semibold">Historical simulated result</h2>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <Meta label="Ending simulated value" value={result.ending_value} />
        <Meta label="Simulated P&L" value={result.simulated_pnl} />
        <Meta label="Historical change" value={`${result.historical_return}%`} />
        <Meta
          label="Events / completed trades"
          value={`${result.event_count} / ${result.completed_trade_count}`}
        />
        <Meta label="Maximum drawdown" value={`${result.maximum_drawdown}%`} />
        <Meta label="Historical volatility" value={result.volatility ?? "Unavailable"} />
        <Meta label="Turnover" value={`${result.turnover}%`} />
        <Meta
          label="Benchmark historical change"
          value={
            result.benchmark_return === null ? "Not configured" : `${result.benchmark_return}%`
          }
        />
        <Meta label="Completeness" value={result.completeness} />
      </dl>
    </article>
  );
}

function ExplanationPanel({
  explanations,
  runId,
  permissions,
  busy,
  mutate,
}: {
  explanations: Explanation[];
  runId: string;
  permissions: Permissions | null;
  busy: boolean;
  mutate: Mutate;
}) {
  return (
    <section>
      {permissions?.can_explain ? (
        <button
          disabled={busy}
          className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
          onClick={() =>
            void mutate(async (auth) => {
              await atlasApi(`/research/backtests/${runId}/explanations`, auth, {
                method: "POST",
                headers: { "Idempotency-Key": idempotencyKey() },
                body: JSON.stringify({ explanation_type: "run_summary" }),
              });
            })
          }
        >
          {busy ? "Generating…" : "Generate local run explanation"}
        </button>
      ) : (
        <p className="text-sm text-slate-400">
          Explanation generation is disabled or not permitted.
        </p>
      )}
      <div className="mt-4 grid gap-4">
        {explanations.length ? (
          explanations.map((item) => (
            <article className="atlas-panel p-6" key={item.id}>
              <h2 className="font-semibold">{item.explanation_type}</h2>
              <p className="mt-3 whitespace-pre-wrap">{item.explanation_text}</p>
              <p className="mt-4 text-sm text-amber-100">{item.limitations}</p>
              <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-3">
                <Meta label="Engine" value={`${item.engine_identifier} ${item.engine_version}`} />
                <Meta label="Template" value={item.template_version} />
                <Meta label="Generated" value={new Date(item.generated_at).toLocaleString()} />
              </dl>
            </article>
          ))
        ) : (
          <Empty>No local explanations have been generated.</Empty>
        )}
      </div>
    </section>
  );
}

function AuditPanel({ events, permissions }: { events: Audit[]; permissions: Permissions | null }) {
  if (!permissions?.can_read_audit)
    return <Empty>Research audit history is restricted to authorised users.</Empty>;
  return (
    <div className="atlas-panel overflow-x-auto p-6">
      <table className="w-full text-left text-sm">
        <caption className="mb-3 text-left font-semibold">
          Append-only research audit history
        </caption>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Event</th>
            <th>Actor</th>
            <th>Target</th>
          </tr>
        </thead>
        <tbody>
          {events.length ? (
            events.map((event) => (
              <tr key={event.id}>
                <td>{new Date(event.created_at).toLocaleString()}</td>
                <td>{event.event_type}</td>
                <td>{event.actor_user_id}</td>
                <td>{event.target_id ?? "—"}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={4}>No audit events are available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ComparisonPanel({
  data,
  busy,
  mutate,
  announce,
}: {
  data: { tenant: Organisation | null; runs: Run[] };
  busy: boolean;
  mutate: Mutate;
  announce: (value: string) => void;
}) {
  const [comparison, setComparison] = useState<{
    runs: Result[];
    comparable: boolean;
    comparison_basis: string;
  } | null>(null);
  if (!data.tenant) return null;
  const completed = data.runs.filter((run) => run.status === "completed");
  return (
    <section>
      <form
        className="atlas-panel p-6"
        onSubmit={(event) => {
          event.preventDefault();
          const selected = new FormData(event.currentTarget).getAll("runs");
          if (selected.length !== 2) {
            announce("Select exactly two completed historical runs.");
            return;
          }
          void mutate(async (auth) => {
            setComparison(
              await atlasApi("/research/backtests/compare", auth, {
                method: "POST",
                body: JSON.stringify({ run_ids: selected }),
              }),
            );
          });
        }}
      >
        <fieldset>
          <legend className="font-display text-2xl font-semibold">Select two completed runs</legend>
          <div className="mt-4 grid gap-3">
            {completed.map((run) => (
              <label className="atlas-panel flex gap-3 p-4" key={run.id}>
                <input name="runs" type="checkbox" value={run.id} />
                <span>
                  {run.start_date} to {run.end_date} · {run.base_currency} · {run.id}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <button
          disabled={busy || completed.length < 2}
          className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950"
        >
          Compare historical results
        </button>
      </form>
      {comparison ? (
        <article className="atlas-panel mt-5 p-6">
          <h2 className="font-semibold">Neutral descriptive comparison</h2>
          <p className="mt-2">{comparison.comparison_basis}</p>
          <p className="mt-2 text-amber-100">
            {comparison.comparable
              ? "Periods and currencies are comparable."
              : "Warning: periods or currencies are not directly comparable."}
          </p>
          {comparison.runs.map((result) => (
            <ResultSummary result={result} key={result.run_id} />
          ))}
        </article>
      ) : null}
    </section>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-slate-400">{label}</dt>
      <dd className="break-all text-slate-100">{value}</dd>
    </div>
  );
}
function Empty({ children }: { children: ReactNode }) {
  return <div className="atlas-panel mt-4 p-6 text-slate-400">{children}</div>;
}
