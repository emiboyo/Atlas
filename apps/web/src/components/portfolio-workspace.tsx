"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";
import { PortfolioNotice } from "@/components/portfolio-notice";

type View = "overview" | "transactions" | "holdings" | "analytics" | "audit";
type Portfolio = {
  id: string;
  name: string;
  description: string | null;
  base_currency: string;
  status: string;
  version: number;
};
type Permissions = {
  can_update: boolean;
  can_archive: boolean;
  can_create_transaction: boolean;
  can_read_audit: boolean;
};
type Transaction = {
  id: string;
  sequence: number;
  transaction_type: string;
  status: string;
  currency: string;
  net_amount: string;
  effective_at: string;
};
type Holding = {
  listing_id: string;
  symbol: string;
  exchange: string;
  currency: string;
  quantity: string;
  average_cost_per_unit: string;
  cost_basis: string;
  realised_simulated_pnl: string;
  position_status: string;
};
type ValuedHolding = Holding & {
  market_value: string | null;
  unrealised_simulated_pnl: string | null;
  data_status: string;
  valuation_status: string;
};
type Valuation = {
  base_currency: string;
  base_currency_total: string | null;
  completeness: string;
  virtual_cash_by_currency: { currency: string; amount: string }[];
  positions: ValuedHolding[];
  unconverted_currencies: string[];
  missing_listing_ids: string[];
  stale_listing_ids: string[];
};
type Analytics = {
  allocation: { label: string; currency: string; value: string; percentage: string | null }[];
  realised_simulated_pnl: string;
  unrealised_simulated_pnl: string | null;
  currency_exposure: Record<string, string>;
  data_complete: boolean;
  disclaimer: string;
};
type AuditEvent = {
  id: string;
  event_type: string;
  created_at: string;
  request_id: string | null;
};

const tabs: { key: View; label: string; suffix: string }[] = [
  { key: "overview", label: "Overview", suffix: "" },
  { key: "transactions", label: "Transactions", suffix: "/transactions" },
  { key: "holdings", label: "Holdings", suffix: "/holdings" },
  { key: "analytics", label: "Analytics", suffix: "/analytics" },
  { key: "audit", label: "Audit history", suffix: "/audit" },
];

export function PortfolioWorkspace({
  portfolioId,
  view = "overview",
}: {
  portfolioId: string;
  view?: View;
}) {
  const { getToken } = useAuth();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [permissions, setPermissions] = useState<Permissions | null>(null);
  const [valuation, setValuation] = useState<Valuation | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [message, setMessage] = useState("Loading simulated portfolio…");

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const [portfolioResult, permissionResult] = await Promise.all([
          atlasApi<Portfolio>(`/portfolios/${portfolioId}`, token),
          atlasApi<Permissions>(`/portfolios/${portfolioId}/effective-permissions`, token),
        ]);
        if (!active) return;
        setPortfolio(portfolioResult);
        setPermissions(permissionResult);
        if (view === "overview") {
          setValuation(await atlasApi<Valuation>(`/portfolios/${portfolioId}/valuation`, token));
        } else if (view === "transactions") {
          const page = await atlasApi<{ items: Transaction[] }>(
            `/portfolios/${portfolioId}/transactions`,
            token,
          );
          setTransactions(page.items);
        } else if (view === "holdings") {
          setHoldings(await atlasApi<Holding[]>(`/portfolios/${portfolioId}/holdings`, token));
        } else if (view === "analytics") {
          setAnalytics(await atlasApi<Analytics>(`/portfolios/${portfolioId}/analytics`, token));
        } else if (view === "audit" && permissionResult.can_read_audit) {
          setEvents(await atlasApi<AuditEvent[]>(`/portfolios/${portfolioId}/audit-events`, token));
        }
        setMessage("");
      } catch (error) {
        if (active) {
          setMessage(
            error instanceof Error ? error.message : "The simulated portfolio is unavailable.",
          );
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken, portfolioId, view]);

  async function archive() {
    if (!window.confirm("Archive this simulated portfolio? New transactions will be blocked.")) {
      return;
    }
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      setPortfolio(
        await atlasApi<Portfolio>(`/portfolios/${portfolioId}/archive`, token, { method: "POST" }),
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Archive failed.");
    }
  }

  if (!portfolio) {
    return (
      <div>
        <PortfolioNotice />
        <p role="status" className="mt-6 text-slate-300">
          {message}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PortfolioNotice />
      <header className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm uppercase tracking-[0.18em] text-cyan-300">
            Simulated · {portfolio.status}
          </p>
          <h1 className="font-display mt-2 text-3xl font-semibold">{portfolio.name}</h1>
          <p className="mt-2 text-slate-400">
            {portfolio.description || "No description"} · Base currency {portfolio.base_currency}
          </p>
        </div>
        {permissions?.can_archive && portfolio.status === "active" ? (
          <button
            onClick={() => void archive()}
            className="rounded-xl border border-white/15 px-4 py-2 text-sm"
          >
            Archive simulated portfolio
          </button>
        ) : null}
      </header>
      <nav aria-label="Portfolio sections" className="flex gap-2 overflow-x-auto">
        {tabs
          .filter((tab) => tab.key !== "audit" || permissions?.can_read_audit)
          .map((tab) => (
            <Link
              key={tab.key}
              href={`/app/portfolios/${portfolioId}${tab.suffix}` as Route}
              aria-current={view === tab.key ? "page" : undefined}
              className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm ${
                view === tab.key ? "bg-cyan-300 text-slate-950" : "bg-white/5 text-slate-300"
              }`}
            >
              {tab.label}
            </Link>
          ))}
      </nav>
      <p role="status" className="text-sm text-slate-400">
        {message}
      </p>
      {view === "overview" ? (
        <Overview valuation={valuation} />
      ) : view === "transactions" ? (
        <Transactions
          items={transactions}
          portfolioId={portfolioId}
          canCreate={Boolean(permissions?.can_create_transaction && portfolio.status === "active")}
        />
      ) : view === "holdings" ? (
        <Holdings items={holdings} />
      ) : view === "analytics" ? (
        <AnalyticsPanel analytics={analytics} />
      ) : (
        <AuditPanel events={events} canRead={Boolean(permissions?.can_read_audit)} />
      )}
    </div>
  );
}

function Overview({ valuation }: { valuation: Valuation | null }) {
  if (!valuation) return <p className="text-slate-400">Valuation is loading or unavailable.</p>;
  const cash = valuation.virtual_cash_by_currency[0];
  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <SummaryCard
        label="Simulated portfolio value"
        value={
          valuation.base_currency_total === null
            ? "Unavailable / incomplete"
            : `${valuation.base_currency} ${valuation.base_currency_total}`
        }
        detail={`Completeness: ${valuation.completeness}`}
      />
      <SummaryCard
        label="Virtual cash"
        value={cash ? `${cash.currency} ${cash.amount}` : "Unavailable"}
        detail="Internal simulated accounting balance"
      />
      <SummaryCard
        label="Data quality"
        value={
          valuation.missing_listing_ids.length
            ? `${valuation.missing_listing_ids.length} missing prices`
            : valuation.stale_listing_ids.length
              ? `${valuation.stale_listing_ids.length} stale prices`
              : "No missing prices"
        }
        detail={
          valuation.unconverted_currencies.length
            ? `Unconverted: ${valuation.unconverted_currencies.join(", ")}`
            : "No silent currency conversion"
        }
      />
      <section className="lg:col-span-3">
        <ValuationTable items={valuation.positions} />
      </section>
    </div>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <h2 className="text-sm text-slate-400">{label}</h2>
      <p className="mt-2 text-xl font-semibold">{value}</p>
      <p className="mt-2 text-xs text-slate-500">{detail}</p>
    </section>
  );
}

function Transactions({
  items,
  portfolioId,
  canCreate,
}: {
  items: Transaction[];
  portfolioId: string;
  canCreate: boolean;
}) {
  const { getToken } = useAuth();
  const [reversalMessage, setReversalMessage] = useState("");

  async function reverse(item: Transaction) {
    if (!window.confirm("Post an equal-and-opposite compensating simulated transaction?")) return;
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi(`/portfolios/${portfolioId}/transactions/${item.id}/reverse`, token, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({
          reason: "User-requested correction of simulated activity",
          effective_at: new Date().toISOString(),
        }),
      });
      window.location.reload();
    } catch (error) {
      setReversalMessage(error instanceof Error ? error.message : "Reversal failed.");
    }
  }

  return (
    <section>
      <div className="flex justify-between gap-4">
        <h2 className="font-display text-2xl font-semibold">Immutable transaction history</h2>
        {canCreate ? (
          <Link
            href={`/app/portfolios/${portfolioId}/transactions/new` as Route}
            className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
          >
            Record simulated activity
          </Link>
        ) : null}
      </div>
      <div className="mt-5 overflow-x-auto">
        <p role="status" className="mb-3 text-sm text-rose-300">
          {reversalMessage}
        </p>
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Posted simulated portfolio transactions</caption>
          <thead className="text-slate-400">
            <tr>
              <th className="p-3">Sequence</th>
              <th className="p-3">Type</th>
              <th className="p-3">Amount</th>
              <th className="p-3">Status</th>
              <th className="p-3">Effective time</th>
              {canCreate ? <th className="p-3">Correction</th> : null}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-white/10">
                <td className="p-3">{item.sequence}</td>
                <td className="p-3">{item.transaction_type.replaceAll("_", " ")}</td>
                <td className="p-3">
                  {item.currency} {item.net_amount}
                </td>
                <td className="p-3">{item.status}</td>
                <td className="p-3">{new Date(item.effective_at).toLocaleString()}</td>
                {canCreate ? (
                  <td className="p-3">
                    {item.status === "posted" && item.transaction_type !== "reversal" ? (
                      <button
                        onClick={() => void reverse(item)}
                        className="rounded-lg border border-white/15 px-3 py-1.5"
                      >
                        Record compensating reversal
                      </button>
                    ) : (
                      "Not available"
                    )}
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!items.length ? <p className="mt-5 text-slate-400">No simulated transactions yet.</p> : null}
    </section>
  );
}

function Holdings({ items }: { items: Holding[] }) {
  return (
    <section className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <caption className="font-display mb-4 text-left text-2xl font-semibold">
          Simulated holdings and weighted-average cost
        </caption>
        <thead className="text-slate-400">
          <tr>
            {["Listing", "Quantity", "Average cost", "Cost basis", "Realised P&L", "State"].map(
              (heading) => (
                <th key={heading} className="p-3">
                  {heading}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.listing_id} className="border-t border-white/10">
              <td className="p-3">
                {item.symbol} · {item.exchange}
              </td>
              <td className="p-3">{item.quantity}</td>
              <td className="p-3">
                {item.currency} {item.average_cost_per_unit}
              </td>
              <td className="p-3">
                {item.currency} {item.cost_basis}
              </td>
              <td className="p-3">
                {item.currency} {item.realised_simulated_pnl}
              </td>
              <td className="p-3">{item.position_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length ? <p className="mt-5 text-slate-400">No simulated holdings yet.</p> : null}
    </section>
  );
}

function ValuationTable({ items }: { items: ValuedHolding[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-white/10">
      <table className="w-full text-left text-sm">
        <caption className="p-4 text-left font-semibold">
          Simulated holding valuation with explicit data states
        </caption>
        <thead className="text-slate-400">
          <tr>
            <th className="p-3">Listing</th>
            <th className="p-3">Quantity</th>
            <th className="p-3">Market value</th>
            <th className="p-3">Unrealised P&amp;L</th>
            <th className="p-3">Data state</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.listing_id} className="border-t border-white/10">
              <td className="p-3">
                {item.symbol} · {item.exchange}
              </td>
              <td className="p-3">{item.quantity}</td>
              <td className="p-3">
                {item.market_value === null
                  ? "Unavailable"
                  : `${item.currency} ${item.market_value}`}
              </td>
              <td className="p-3">
                {item.unrealised_simulated_pnl === null
                  ? "Unavailable"
                  : `${item.currency} ${item.unrealised_simulated_pnl}`}
              </td>
              <td className="p-3">
                <span className="font-medium">{item.valuation_status}</span> · {item.data_status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AnalyticsPanel({ analytics }: { analytics: Analytics | null }) {
  if (!analytics) return <p className="text-slate-400">Descriptive analytics unavailable.</p>;
  return (
    <div className="space-y-6">
      <section aria-labelledby="allocation-title">
        <h2 id="allocation-title" className="font-display text-2xl font-semibold">
          Descriptive allocation
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Text alternative: allocation values are listed below; bars are decorative.
        </p>
        <ul className="mt-5 space-y-3">
          {analytics.allocation.map((item) => (
            <li key={`${item.label}-${item.currency}`}>
              <div className="flex justify-between gap-4 text-sm">
                <span>{item.label}</span>
                <span>
                  {item.currency} {item.value} · {item.percentage ?? "unavailable"}%
                </span>
              </div>
              <div aria-hidden="true" className="mt-2 h-2 rounded bg-white/10">
                <div
                  className="h-full rounded bg-cyan-300"
                  style={{ width: `${Math.min(Number(item.percentage ?? 0), 100)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </section>
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard
          label="Realised simulated P&L"
          value={analytics.realised_simulated_pnl}
          detail="Historical simulated transactions only"
        />
        <SummaryCard
          label="Unrealised simulated P&L"
          value={analytics.unrealised_simulated_pnl ?? "Unavailable"}
          detail="Unavailable when valuation data is incomplete"
        />
        <SummaryCard
          label="Data completeness"
          value={analytics.data_complete ? "Complete" : "Incomplete"}
          detail="Missing and unconverted values are excluded"
        />
      </div>
      <p className="rounded-xl border border-white/10 p-4 text-sm text-slate-400">
        Volatility and maximum drawdown use available valuation snapshots, disclose their time
        range, frequency, observation count, and missing-data policy. {analytics.disclaimer}
      </p>
    </div>
  );
}

function AuditPanel({ events, canRead }: { events: AuditEvent[]; canRead: boolean }) {
  if (!canRead) {
    return <p className="text-slate-400">Audit history is restricted to owners and admins.</p>;
  }
  return (
    <section>
      <h2 className="font-display text-2xl font-semibold">Append-only portfolio audit history</h2>
      <ol className="mt-5 space-y-3">
        {events.map((event) => (
          <li key={event.id} className="rounded-xl border border-white/10 p-4">
            <p className="font-medium">{event.event_type}</p>
            <p className="mt-1 text-xs text-slate-400">
              {new Date(event.created_at).toLocaleString()} · Request{" "}
              {event.request_id ?? "not supplied"}
            </p>
          </li>
        ))}
      </ol>
      {!events.length ? <p className="mt-5 text-slate-400">No visible audit events.</p> : null}
    </section>
  );
}
