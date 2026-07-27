"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";

type Organisation = { id: string; name: string; role: string };
type Watchlist = {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  status: string;
  items: { id: string }[];
};

export function WatchlistBrowser() {
  const { getToken } = useAuth();
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("Loading workspaces…");

  async function loadWatchlists(selectedTenant: string) {
    const token = await getToken();
    if (!token) throw new Error("Authentication is required.");
    const result = await atlasApi<Watchlist[]>(
      `/watchlists?tenant_id=${encodeURIComponent(selectedTenant)}`,
      token,
    );
    setWatchlists(result);
    setMessage(result.length ? "" : "No watchlists in this workspace.");
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
        if (selected) await loadWatchlists(selected);
        else setMessage("No authorised workspace is available.");
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "Watchlists unavailable.");
      }
    })();
    return () => {
      active = false;
    };
    // loadWatchlists is intentionally invoked only after the initial workspace resolution.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getToken]);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Select an authorised workspace.");
      await atlasApi("/watchlists", token, {
        method: "POST",
        body: JSON.stringify({ tenant_id: tenantId, name }),
      });
      setName("");
      await loadWatchlists(tenantId);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Watchlist could not be created.");
    }
  }

  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section>
        <label className="block">
          <span className="text-sm text-slate-300">Workspace</span>
          <select
            className="atlas-input mt-2 w-full"
            value={tenantId}
            onChange={(event) => {
              setTenantId(event.target.value);
              void loadWatchlists(event.target.value);
            }}
          >
            {organisations.map((organisation) => (
              <option key={organisation.id} value={organisation.id}>
                {organisation.name} · {organisation.role}
              </option>
            ))}
          </select>
        </label>
        <p role="status" className="mt-3 text-sm text-slate-400">
          {message}
        </p>
        <div className="mt-5 grid gap-3">
          {watchlists.map((watchlist) => (
            <Link
              key={watchlist.id}
              href={`/app/watchlists/${watchlist.id}` as Route}
              className="rounded-xl border border-white/10 p-5 hover:border-cyan-300/40"
            >
              <h2 className="font-semibold">{watchlist.name}</h2>
              <p className="mt-1 text-sm text-slate-400">
                {watchlist.items.length} listings · {watchlist.status}
              </p>
            </Link>
          ))}
        </div>
      </section>
      <form
        onSubmit={(event) => void create(event)}
        className="h-fit rounded-2xl border border-white/10 p-6"
      >
        <h2 className="font-display text-xl font-semibold">Create watchlist</h2>
        <label className="mt-5 block">
          <span className="text-sm text-slate-300">Watchlist name</span>
          <input
            className="atlas-input mt-2 w-full"
            value={name}
            minLength={1}
            maxLength={120}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        <button className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950">
          Create
        </button>
      </form>
    </div>
  );
}
