"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";

type SearchItem = {
  instrument_id: string;
  canonical_name: string;
  short_name: string | null;
  asset_class: string;
  status: string;
  listing: {
    id: string;
    symbol: string;
    currency: string;
    status: string;
    data_availability: string;
    exchange: { mic: string; name: string };
  };
};

export function MarketSearch() {
  const { getToken } = useAuth();
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<SearchItem[]>([]);
  const [message, setMessage] = useState(
    "Search by symbol, instrument name, venue, MIC, or verified identifier.",
  );
  const [loading, setLoading] = useState(false);

  async function search(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      const result = await atlasApi<{ items: SearchItem[]; total: number }>(
        `/market/instruments/search?q=${encodeURIComponent(query.trim())}`,
        token,
      );
      setItems(result.items);
      setMessage(result.total ? `${result.total} listing results.` : "No instruments matched.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Search is unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-8">
      <div className="rounded-2xl border border-amber-300/30 bg-amber-300/10 p-4 text-sm text-amber-100">
        Simulated development data. Values are deterministic test fixtures, not real-time market
        information and not investment advice.
      </div>
      <form
        onSubmit={(event) => void search(event)}
        className="mt-6 flex flex-col gap-3 sm:flex-row"
      >
        <label className="flex-1">
          <span className="sr-only">Search instruments</span>
          <input
            className="atlas-input w-full"
            value={query}
            minLength={2}
            maxLength={100}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="NOVA, XDEV, development equity…"
            required
          />
        </label>
        <button
          className="rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Searching…" : "Search catalogue"}
        </button>
      </form>
      <p role="status" className="mt-3 text-sm text-slate-400">
        {message}
      </p>
      <div className="mt-6 overflow-x-auto rounded-2xl border border-white/10">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-white/5 text-slate-300">
            <tr>
              <th className="p-4">Symbol</th>
              <th className="p-4">Instrument</th>
              <th className="p-4">Asset class</th>
              <th className="p-4">Venue</th>
              <th className="p-4">Currency</th>
              <th className="p-4">Data</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.listing.id} className="border-t border-white/10">
                <td className="p-4 font-mono text-cyan-200">{item.listing.symbol}</td>
                <td className="p-4">
                  <Link
                    href={`/app/markets/instruments/${item.instrument_id}` as Route}
                    className="font-medium text-white hover:text-cyan-200"
                  >
                    {item.canonical_name}
                  </Link>
                </td>
                <td className="p-4">{item.asset_class.replaceAll("_", " ")}</td>
                <td className="p-4">
                  {item.listing.exchange.mic} · {item.listing.exchange.name}
                </td>
                <td className="p-4">{item.listing.currency}</td>
                <td className="p-4 capitalize">{item.listing.data_availability}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
