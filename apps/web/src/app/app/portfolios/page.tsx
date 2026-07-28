import { PortfolioBrowser } from "@/components/portfolio-browser";

export default function PortfoliosPage() {
  return (
    <section>
      <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Private development</p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Simulated portfolios</h1>
      <p className="mt-3 max-w-2xl text-slate-400">
        Tenant-isolated paper accounting and descriptive read-only analytics.
      </p>
      <div className="mt-8">
        <PortfolioBrowser />
      </div>
    </section>
  );
}
