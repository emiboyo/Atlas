"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";
import { MarketDataState } from "@/components/market-data-state";

type Listing = {
  id: string;
  symbol: string;
  currency: string;
  status: string;
  exchange: { mic: string; name: string; timezone: string };
};
type Instrument = {
  id: string;
  canonical_name: string;
  description: string | null;
  asset_class: string;
  primary_currency: string;
  status: string;
  listings: Listing[];
};
type Quote = {
  price: string | null;
  currency: string;
  provider_timestamp: string;
  received_at: string;
  data_status: string;
  delay_seconds?: number | null;
  is_stale: boolean;
  source_label: string;
  disclaimer: string;
};

export function MarketInstrument({ instrumentId }: { instrumentId: string }) {
  const { getToken } = useAuth();
  const [instrument, setInstrument] = useState<Instrument | null>(null);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [message, setMessage] = useState("Loading instrument…");

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const detail = await atlasApi<Instrument>(`/market/instruments/${instrumentId}`, token);
        const latest = detail.listings[0]
          ? await atlasApi<Quote>(`/market/listings/${detail.listings[0].id}/quote`, token)
          : null;
        if (active) {
          setInstrument(detail);
          setQuote(latest);
          setMessage("");
        }
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "Instrument unavailable.");
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken, instrumentId]);

  if (!instrument) return <p role="status">{message}</p>;
  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">
          {instrument.asset_class.replaceAll("_", " ")}
        </p>
        <h1 className="font-display mt-2 text-4xl font-semibold">{instrument.canonical_name}</h1>
        <p className="mt-3 max-w-3xl text-slate-300">{instrument.description}</p>
      </header>
      <MarketDataState
        status={quote?.data_status ?? "unavailable"}
        providerTimestamp={quote?.provider_timestamp}
        delaySeconds={quote?.delay_seconds}
        message={quote?.disclaimer}
      />
      {quote ? (
        <section aria-labelledby="quote-title" className="rounded-2xl border border-white/10 p-6">
          <h2 id="quote-title" className="font-display text-xl font-semibold">
            Latest available snapshot
          </h2>
          <p className="mt-4 text-3xl font-semibold">
            {quote.price ?? "Unavailable"} {quote.currency}
          </p>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-400">Status</dt>
              <dd className="capitalize">
                {quote.data_status}
                {quote.is_stale ? " · stale" : ""}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">Provider timestamp</dt>
              <dd>{new Date(quote.provider_timestamp).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-slate-400">Source</dt>
              <dd>{quote.source_label}</dd>
            </div>
          </dl>
          <p className="mt-5 text-xs text-slate-400">{quote.disclaimer}</p>
        </section>
      ) : null}
      <section>
        <h2 className="font-display text-xl font-semibold">Listings</h2>
        <div className="mt-4 grid gap-3">
          {instrument.listings.map((listing) => (
            <Link
              key={listing.id}
              href={`/app/markets/listings/${listing.id}` as Route}
              className="rounded-xl border border-white/10 p-4 hover:border-cyan-300/40"
            >
              <strong>{listing.symbol}</strong> · {listing.exchange.mic} · {listing.currency} ·{" "}
              {listing.status}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
