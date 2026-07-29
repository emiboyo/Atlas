import Link from "next/link";
import { ResearchNotice } from "@/components/research-notice";

export default function ResearchPage() {
  return (
    <section className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Private development</p>
        <h1 className="font-display mt-3 text-4xl font-semibold">Historical strategy research</h1>
        <p className="mt-3 max-w-3xl text-slate-400">
          Define immutable rules, run deterministic long-only simulations, and inspect reproducible
          historical evidence.
        </p>
      </div>
      <ResearchNotice />
      <div className="grid gap-4 md:grid-cols-3">
        <Link className="atlas-panel p-6" href="/app/research/strategies">
          <h2 className="text-xl font-semibold">Strategies</h2>
          <p className="mt-2 text-sm text-slate-400">Research hypotheses and immutable versions.</p>
        </Link>
        <Link className="atlas-panel p-6" href="/app/research/backtests">
          <h2 className="text-xl font-semibold">Backtests</h2>
          <p className="mt-2 text-sm text-slate-400">Explicit assumptions and reproducible runs.</p>
        </Link>
        <Link className="atlas-panel p-6" href="/app/research/compare">
          <h2 className="text-xl font-semibold">Compare</h2>
          <p className="mt-2 text-sm text-slate-400">Neutral historical result comparison.</p>
        </Link>
      </div>
    </section>
  );
}
