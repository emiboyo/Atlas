import { WatchlistBrowser } from "@/components/watchlist-browser";

export default function WatchlistsPage() {
  return (
    <section>
      <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Workspace research</p>
      <h1 className="font-display mt-2 text-4xl font-semibold">Watchlists</h1>
      <p className="mt-3 max-w-3xl text-slate-300">
        Organise venue-specific listings inside workspaces you are authorised to access.
      </p>
      <WatchlistBrowser />
    </section>
  );
}
