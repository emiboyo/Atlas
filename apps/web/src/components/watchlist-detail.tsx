"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import { atlasApi } from "@/lib/api-client";

type Watchlist = {
  id: string;
  name: string;
  description: string | null;
  status: string;
  items: {
    id: string;
    listing_id: string;
    position: number;
    notes: string | null;
  }[];
};

export function WatchlistDetail({ watchlistId }: { watchlistId: string }) {
  const { getToken } = useAuth();
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [listingId, setListingId] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("Loading watchlist…");

  async function load() {
    const token = await getToken();
    if (!token) throw new Error("Authentication is required.");
    const result = await atlasApi<Watchlist>(`/watchlists/${watchlistId}`, token);
    setWatchlist(result);
    setMessage("");
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const result = await atlasApi<Watchlist>(`/watchlists/${watchlistId}`, token);
        if (active) {
          setWatchlist(result);
          setMessage("");
        }
      } catch (error) {
        if (active) {
          setMessage(error instanceof Error ? error.message : "Watchlist unavailable.");
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken, watchlistId]);

  async function add(event: FormEvent) {
    event.preventDefault();
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi(`/watchlists/${watchlistId}/items`, token, {
        method: "POST",
        body: JSON.stringify({ listing_id: listingId.trim(), notes: notes || null }),
      });
      setListingId("");
      setNotes("");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Listing could not be added.");
    }
  }

  async function remove(itemId: string) {
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi(`/watchlists/${watchlistId}/items/${itemId}`, token, {
        method: "DELETE",
      });
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Listing could not be removed.");
    }
  }

  async function move(itemId: string, direction: -1 | 1) {
    if (!watchlist) return;
    const ordered = [...watchlist.items].sort((a, b) => a.position - b.position);
    const index = ordered.findIndex((item) => item.id === itemId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ordered.length) return;
    [ordered[index], ordered[target]] = [ordered[target]!, ordered[index]!];
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi(`/watchlists/${watchlistId}/items/reorder`, token, {
        method: "PATCH",
        body: JSON.stringify({ item_ids: ordered.map((item) => item.id) }),
      });
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Order could not be updated.");
    }
  }

  if (!watchlist) return <p role="status">{message}</p>;
  return (
    <div>
      <header>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Tenant watchlist</p>
        <h1 className="font-display mt-2 text-4xl font-semibold">{watchlist.name}</h1>
        <p className="mt-2 text-slate-300">{watchlist.description ?? "No description."}</p>
      </header>
      <p role="status" className="mt-4 text-sm text-slate-400">
        {message}
      </p>
      <section className="mt-8">
        <h2 className="font-display text-xl font-semibold">Listings</h2>
        <div className="mt-4 grid gap-3">
          {watchlist.items.map((item, index) => (
            <article key={item.id} className="rounded-xl border border-white/10 p-4">
              <p className="font-mono text-sm text-cyan-200">{item.listing_id}</p>
              <p className="mt-1 text-sm text-slate-400">{item.notes ?? "No notes."}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  aria-label={`Move listing ${index + 1} up`}
                  onClick={() => void move(item.id, -1)}
                  className="rounded-lg border border-white/15 px-3 py-2 text-sm"
                >
                  Move up
                </button>
                <button
                  type="button"
                  aria-label={`Move listing ${index + 1} down`}
                  onClick={() => void move(item.id, 1)}
                  className="rounded-lg border border-white/15 px-3 py-2 text-sm"
                >
                  Move down
                </button>
                <button
                  type="button"
                  onClick={() => void remove(item.id)}
                  className="rounded-lg border border-red-300/30 px-3 py-2 text-sm text-red-200"
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
          {!watchlist.items.length ? (
            <p className="rounded-xl border border-dashed border-white/15 p-6 text-slate-400">
              This watchlist is empty.
            </p>
          ) : null}
        </div>
      </section>
      <form
        onSubmit={(event) => void add(event)}
        className="mt-8 max-w-xl rounded-2xl border border-white/10 p-6"
      >
        <h2 className="font-display text-xl font-semibold">Add a catalogue listing</h2>
        <label className="mt-5 block">
          <span className="text-sm text-slate-300">Listing ID</span>
          <input
            className="atlas-input mt-2 w-full"
            value={listingId}
            onChange={(event) => setListingId(event.target.value)}
            placeholder="Use the listing ID from market search"
            required
          />
        </label>
        <label className="mt-4 block">
          <span className="text-sm text-slate-300">Notes</span>
          <textarea
            className="atlas-input mt-2 min-h-24 w-full"
            value={notes}
            maxLength={500}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
        <button className="mt-5 rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-slate-950">
          Add listing
        </button>
      </form>
    </div>
  );
}
