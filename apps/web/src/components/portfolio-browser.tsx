"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";
import { PortfolioNotice } from "@/components/portfolio-notice";

type Organisation = { id: string; name: string; role: string };
type Portfolio = {
  id: string;
  name: string;
  description: string | null;
  base_currency: string;
  status: string;
};

export function PortfolioBrowser({ creationOnly = false }: { creationOnly?: boolean }) {
  const { getToken } = useAuth();
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [currency, setCurrency] = useState("GBP");
  const [message, setMessage] = useState("Loading authorised workspaces…");
  const [submitting, setSubmitting] = useState(false);

  async function loadPortfolios(selectedTenant: string) {
    const token = await getToken();
    if (!token) throw new Error("Authentication is required.");
    const page = await atlasApi<{ items: Portfolio[] }>(
      `/portfolios?tenant_id=${encodeURIComponent(selectedTenant)}`,
      token,
    );
    setPortfolios(page.items);
    setMessage(page.items.length ? "" : "No simulated portfolios in this workspace.");
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const page = await atlasApi<{ items: Organisation[] }>("/organisations", token);
        if (!active) return;
        setOrganisations(page.items);
        const selected = page.items[0]?.id ?? "";
        setTenantId(selected);
        if (selected && !creationOnly) await loadPortfolios(selected);
        else setMessage(selected ? "" : "No authorised workspace is available.");
      } catch (error) {
        if (active) {
          setMessage(error instanceof Error ? error.message : "Simulated portfolios unavailable.");
        }
      }
    })();
    return () => {
      active = false;
    };
    // The initial workspace resolution intentionally owns the first portfolio request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [creationOnly, getToken]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Select an authorised workspace.");
      const created = await atlasApi<Portfolio>("/portfolios", token, {
        method: "POST",
        body: JSON.stringify({
          tenant_id: tenantId,
          name,
          description: description || null,
          base_currency: currency,
        }),
      });
      window.location.assign(`/app/portfolios/${created.id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The portfolio could not be created.");
      document.querySelector<HTMLElement>('[role="status"]')?.focus();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <PortfolioNotice />
      <label className="block max-w-xl">
        <span className="text-sm text-slate-300">Workspace</span>
        <select
          className="atlas-input mt-2"
          value={tenantId}
          onChange={(event) => {
            setTenantId(event.target.value);
            if (!creationOnly) void loadPortfolios(event.target.value);
          }}
        >
          {organisations.map((organisation) => (
            <option key={organisation.id} value={organisation.id}>
              {organisation.name} · {organisation.role}
            </option>
          ))}
        </select>
      </label>
      <p role="status" tabIndex={-1} className="text-sm text-slate-400">
        {message}
      </p>
      {!creationOnly ? (
        <section aria-labelledby="portfolio-list-title">
          <div className="flex items-center justify-between gap-4">
            <h2 id="portfolio-list-title" className="font-display text-2xl font-semibold">
              Simulated portfolios
            </h2>
            <Link
              href={"/app/portfolios/new" as Route}
              className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
            >
              Create simulated portfolio
            </Link>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {portfolios.map((portfolio) => (
              <Link
                key={portfolio.id}
                href={`/app/portfolios/${portfolio.id}` as Route}
                className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 hover:border-cyan-300/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-display text-xl font-semibold">{portfolio.name}</h3>
                  <span className="rounded-full border border-white/15 px-2.5 py-1 text-xs">
                    {portfolio.status}
                  </span>
                </div>
                <p className="mt-3 text-sm text-slate-400">
                  {portfolio.description || "No description"} · Base currency{" "}
                  {portfolio.base_currency}
                </p>
              </Link>
            ))}
          </div>
        </section>
      ) : (
        <form
          onSubmit={(event) => void create(event)}
          className="max-w-2xl rounded-2xl border border-white/10 bg-white/[0.03] p-6"
        >
          <h2 className="font-display text-2xl font-semibold">Create simulated portfolio</h2>
          <div className="mt-6 grid gap-5">
            <label>
              <span className="text-sm text-slate-300">Portfolio name</span>
              <input
                className="atlas-input mt-2"
                value={name}
                minLength={1}
                maxLength={160}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </label>
            <label>
              <span className="text-sm text-slate-300">Description (optional)</span>
              <textarea
                className="atlas-input mt-2 min-h-28"
                value={description}
                maxLength={1000}
                onChange={(event) => setDescription(event.target.value)}
              />
            </label>
            <label>
              <span className="text-sm text-slate-300">Explicit base currency</span>
              <select
                className="atlas-input mt-2"
                value={currency}
                onChange={(event) => setCurrency(event.target.value)}
              >
                {["GBP", "USD", "EUR"].map((code) => (
                  <option key={code}>{code}</option>
                ))}
              </select>
            </label>
          </div>
          <button
            disabled={submitting}
            className="mt-6 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create simulated portfolio"}
          </button>
        </form>
      )}
    </div>
  );
}
