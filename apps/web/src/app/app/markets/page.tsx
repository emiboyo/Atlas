import { MarketSearch } from "@/components/market-search";

export default function MarketsPage() {
  return (
    <section>
      <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Instrument discovery</p>
      <h1 className="font-display mt-2 text-4xl font-semibold">Markets catalogue</h1>
      <p className="mt-3 max-w-3xl text-slate-300">
        Explore Atlas instruments, venue-specific listings, currencies, and clearly labelled
        development market data.
      </p>
      <MarketSearch />
    </section>
  );
}
