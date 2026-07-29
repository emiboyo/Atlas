"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { atlasApi } from "@/lib/api-client";
import { ResearchNotice } from "@/components/research-notice";

type Organisation = { id: string; name: string; role: string };
type Strategy = {
  id: string;
  name: string;
  research_purpose: string;
  status: string;
  current_version_id: string | null;
};

export function ResearchBrowser({ creationOnly = false }: { creationOnly?: boolean }) {
  const { getToken } = useAuth();
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [message, setMessage] = useState("Loading authorised research workspace…");

  async function load(selected: string) {
    const token = await getToken();
    if (!token) throw new Error("Authentication is required.");
    const page = await atlasApi<{ items: Strategy[] }>(
      `/research/strategies?tenant_id=${encodeURIComponent(selected)}`,
      token,
    );
    setStrategies(page.items);
    setMessage(page.items.length ? "" : "No historical research strategies yet.");
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
        if (selected && !creationOnly) await load(selected);
        else setMessage(selected ? "" : "No authorised workspace is available.");
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "Research unavailable.");
      }
    })();
    return () => {
      active = false;
    };
    // Initial workspace resolution owns the first request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [creationOnly, getToken]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    try {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Select an authorised workspace.");
      const strategy = await atlasApi<Strategy>("/research/strategies", token, {
        method: "POST",
        body: JSON.stringify({
          tenant_id: tenantId,
          name,
          research_purpose: purpose,
          description: null,
        }),
      });
      window.location.assign(`/app/research/strategies/${strategy.id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Strategy creation failed.");
      document.querySelector<HTMLElement>('[role="status"]')?.focus();
    }
  }

  return (
    <div className="space-y-7">
      <ResearchNotice />
      <label className="block max-w-xl">
        <span className="text-sm text-slate-300">Research workspace</span>
        <select
          className="atlas-input mt-2"
          value={tenantId}
          onChange={(event) => {
            setTenantId(event.target.value);
            if (!creationOnly) void load(event.target.value);
          }}
        >
          {organisations.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name} · {item.role}
            </option>
          ))}
        </select>
      </label>
      <p role="status" tabIndex={-1} className="text-sm text-slate-400">
        {message}
      </p>
      {creationOnly ? (
        <form onSubmit={(event) => void create(event)} className="atlas-panel max-w-2xl p-6">
          <h2 className="font-display text-2xl font-semibold">New research strategy</h2>
          <div className="mt-5 grid gap-5">
            <label>
              <span className="text-sm text-slate-300">Strategy name</span>
              <input
                className="atlas-input mt-2"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={1}
                maxLength={160}
                required
              />
            </label>
            <label>
              <span className="text-sm text-slate-300">Historical research purpose</span>
              <textarea
                className="atlas-input mt-2 min-h-28"
                value={purpose}
                onChange={(event) => setPurpose(event.target.value)}
                minLength={3}
                maxLength={500}
                required
              />
            </label>
          </div>
          <button className="mt-6 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950">
            Create research strategy
          </button>
        </form>
      ) : (
        <section>
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-2xl font-semibold">Strategies</h2>
            <Link
              href="/app/research/strategies/new"
              className="rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950"
            >
              New strategy
            </Link>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {strategies.map((item) => (
              <Link
                key={item.id}
                href={`/app/research/strategies/${item.id}` as Route}
                className="atlas-panel p-6 hover:border-cyan-300/40"
              >
                <div className="flex justify-between gap-3">
                  <h3 className="font-display text-xl font-semibold">{item.name}</h3>
                  <span className="text-xs uppercase text-slate-400">{item.status}</span>
                </div>
                <p className="mt-3 text-sm text-slate-400">{item.research_purpose}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
