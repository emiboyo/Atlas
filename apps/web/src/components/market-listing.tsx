"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { atlasApi } from "@/lib/api-client";
import { MarketDataState } from "@/components/market-data-state";

type Listing = {
  id: string;
  instrument_id: string;
  symbol: string;
  currency: string;
  status: string;
  exchange: { mic: string; name: string; timezone: string };
};
type Candle = {
  period_start: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number | null;
};
type CandleResult = {
  data_status: string;
  provider: string;
  disclaimer: string;
  candles: Candle[];
};

export function MarketListing({ listingId }: { listingId: string }) {
  const { getToken } = useAuth();
  const [listing, setListing] = useState<Listing | null>(null);
  const [candles, setCandles] = useState<CandleResult | null>(null);
  const [message, setMessage] = useState("Loading listing history…");

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const detail = await atlasApi<Listing>(`/market/listings/${listingId}`, token);
        const history = await atlasApi<CandleResult>(
          `/market/listings/${listingId}/candles?interval=1d&start=2026-01-01T00%3A00%3A00Z&end=2026-01-15T00%3A00%3A00Z`,
          token,
        );
        if (active) {
          setListing(detail);
          setCandles(history);
          setMessage("");
        }
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "History unavailable.");
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken, listingId]);

  if (!listing || !candles) return <p role="status">{message}</p>;
  return (
    <div>
      <header>
        <p className="text-cyan-300">
          {listing.exchange.mic} · {listing.exchange.name}
        </p>
        <h1 className="font-display mt-2 text-4xl font-semibold">{listing.symbol}</h1>
        <p className="mt-2 text-slate-300">
          {listing.currency} · {listing.status} · {listing.exchange.timezone}
        </p>
      </header>
      <div className="mt-8">
        <MarketDataState status={candles.data_status} message={candles.disclaimer} />
      </div>
      <section className="mt-8 overflow-x-auto rounded-2xl border border-white/10">
        <table className="w-full min-w-[700px] text-left text-sm">
          <caption className="p-4 text-left font-semibold">Historical fixture candles</caption>
          <thead className="bg-white/5 text-slate-300">
            <tr>
              <th className="p-3">Period</th>
              <th className="p-3">Open</th>
              <th className="p-3">High</th>
              <th className="p-3">Low</th>
              <th className="p-3">Close</th>
              <th className="p-3">Volume</th>
            </tr>
          </thead>
          <tbody>
            {candles.candles.map((candle) => (
              <tr key={candle.period_start} className="border-t border-white/10">
                <td className="p-3">{new Date(candle.period_start).toLocaleDateString()}</td>
                <td className="p-3">{candle.open}</td>
                <td className="p-3">{candle.high}</td>
                <td className="p-3">{candle.low}</td>
                <td className="p-3">{candle.close}</td>
                <td className="p-3">{candle.volume ?? "Unavailable"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
