"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { atlasApi } from "@/lib/api-client";
import { ProfileForm } from "@/components/profile-form";

export function OnboardingPanel() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function complete() {
    setBusy(true);
    setMessage("");
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      await atlasApi("/onboarding/complete", token, { method: "POST" });
      router.replace("/app");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Onboarding could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <ol className="mt-8 grid gap-3 text-slate-300">
        <li>1. Confirm your basic profile information.</li>
        <li>2. Select locale, timezone, country, and base currency.</li>
        <li>3. Confirm your automatically provisioned personal workspace.</li>
        <li>4. Complete application onboarding.</li>
      </ol>
      <ProfileForm onboarding />
      <div className="mt-8 border-t border-white/10 pt-8">
        <p className="max-w-2xl text-sm text-slate-400">
          Completing onboarding is not KYC verification, suitability assessment, investment
          approval, eligibility to trade, or regulatory approval.
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={() => void complete()}
          className="mt-5 rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Completing…" : "Complete onboarding"}
        </button>
        {message ? (
          <p role="alert" className="mt-4 text-sm text-rose-300">
            {message}
          </p>
        ) : null}
      </div>
    </>
  );
}
