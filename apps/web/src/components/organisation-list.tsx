"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { atlasApi } from "@/lib/api-client";

type Organisation = {
  id: string;
  name: string;
  slug: string;
  organisation_type: "personal" | "team";
  status: string;
  role: string;
};

export function OrganisationList() {
  const { getToken } = useAuth();
  const [items, setItems] = useState<Organisation[]>([]);
  const [message, setMessage] = useState("Loading workspaces…");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  async function load() {
    const token = await getToken();
    if (!token) throw new Error("Authentication is required.");
    const page = await atlasApi<{ items: Organisation[] }>("/organisations", token);
    setItems(page.items);
    setMessage(page.items.length ? "" : "No workspaces are available.");
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const page = await atlasApi<{ items: Organisation[] }>("/organisations", token);
        if (active) {
          setItems(page.items);
          setMessage(page.items.length ? "" : "No workspaces are available.");
        }
      } catch (error) {
        if (active) {
          setMessage(error instanceof Error ? error.message : "Workspaces could not be loaded.");
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken]);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi("/organisations", token, {
        method: "POST",
        body: JSON.stringify({ name, slug }),
      });
      setName("");
      setSlug("");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The workspace could not be created.");
    }
  }

  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section aria-labelledby="workspace-list-title">
        <h2 id="workspace-list-title" className="font-display text-xl font-semibold">
          Your workspaces
        </h2>
        <div className="mt-4 grid gap-3">
          {items.map((item) => (
            <Link
              key={item.id}
              href={`/app/organisations/${item.id}` as Route}
              className="rounded-xl border border-white/10 bg-white/5 p-5 hover:border-cyan-300/40"
            >
              <span className="font-semibold">{item.name}</span>
              <span className="mt-1 block text-sm text-slate-400">
                {item.organisation_type} · {item.role}
              </span>
            </Link>
          ))}
          {message ? (
            <p role="status" className="text-sm text-slate-400">
              {message}
            </p>
          ) : null}
        </div>
      </section>
      <form
        onSubmit={(event) => void create(event)}
        className="rounded-2xl border border-white/10 bg-white/5 p-6"
      >
        <h2 className="font-display text-xl font-semibold">Create a team workspace</h2>
        <label className="mt-5 grid gap-2 text-sm">
          Workspace name
          <input
            required
            maxLength={160}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="atlas-input"
          />
        </label>
        <label className="mt-4 grid gap-2 text-sm">
          Slug
          <input
            required
            pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
            value={slug}
            onChange={(event) => setSlug(event.target.value.toLowerCase())}
            className="atlas-input"
          />
        </label>
        <button className="mt-5 rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950">
          Create workspace
        </button>
      </form>
    </div>
  );
}
