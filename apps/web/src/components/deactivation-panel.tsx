"use client";

import { useState } from "react";
import { useAuth, useClerk } from "@clerk/nextjs";
import { atlasApi } from "@/lib/api-client";

export function DeactivationPanel() {
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");

  async function deactivate() {
    setMessage("");
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi("/me/deactivate", token, {
        method: "POST",
        body: JSON.stringify({ confirmation }),
      });
      await signOut({ redirectUrl: "/" });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Account deactivation failed.");
    }
  }

  return (
    <section className="mt-12 max-w-3xl border-t border-rose-400/20 pt-8">
      <h2 className="font-display text-xl font-semibold text-rose-200">Deactivate account</h2>
      <p className="mt-3 text-sm leading-6 text-slate-400">
        Deactivation blocks normal access but retains audit, membership, and financial-integrity
        records. It is not a personal-data erasure request.
      </p>
      <label className="mt-5 grid max-w-md gap-2 text-sm">
        Type DEACTIVATE to confirm
        <input
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          className="atlas-input"
          autoComplete="off"
        />
      </label>
      <button
        type="button"
        disabled={confirmation !== "DEACTIVATE"}
        onClick={() => void deactivate()}
        className="mt-4 rounded-lg border border-rose-300/40 px-5 py-3 font-semibold text-rose-100 disabled:opacity-40"
      >
        Deactivate my Atlas account
      </button>
      {message ? (
        <p role="alert" className="mt-4 text-sm text-rose-300">
          {message}
        </p>
      ) : null}
    </section>
  );
}
