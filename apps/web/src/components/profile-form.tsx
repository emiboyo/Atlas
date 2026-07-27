"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import { AtlasApiError, atlasApi } from "@/lib/api-client";

type Profile = {
  display_name: string;
  first_name: string | null;
  last_name: string | null;
  preferred_locale: string;
  timezone: string;
  country_of_residence: string | null;
  base_currency: string;
  onboarding_status: string;
};

export function ProfileForm({ onboarding = false }: { onboarding?: boolean }) {
  const { getToken } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState("Loading profile…");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    void getToken()
      .then((token) => {
        if (!token) throw new Error("Authentication is required.");
        return atlasApi<{ profile?: Profile } | Profile>(onboarding ? "/onboarding" : "/me", token);
      })
      .then((result) => {
        if (!active) return;
        const value = "profile" in result && result.profile ? result.profile : (result as Profile);
        setProfile(value);
        setMessage("");
      })
      .catch((error: unknown) => {
        if (active) setMessage(toMessage(error));
      });
    return () => {
      active = false;
    };
  }, [getToken, onboarding]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;
    setBusy(true);
    setMessage("");
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      const updated = await atlasApi<Profile>(
        onboarding ? "/onboarding/profile" : "/me/profile",
        token,
        { method: "PATCH", body: JSON.stringify(profile) },
      );
      setProfile(updated);
      setMessage("Profile saved.");
    } catch (error) {
      setMessage(toMessage(error));
    } finally {
      setBusy(false);
    }
  }

  if (!profile) {
    return <StatusMessage message={message} />;
  }

  return (
    <form
      onSubmit={(event) => void submit(event)}
      className="mt-8 grid max-w-3xl gap-5 md:grid-cols-2"
    >
      <Field label="Display name">
        <input
          required
          maxLength={120}
          value={profile.display_name}
          onChange={(event) => setProfile({ ...profile, display_name: event.target.value })}
          className="atlas-input"
        />
      </Field>
      <Field label="Preferred locale">
        <input
          required
          value={profile.preferred_locale}
          onChange={(event) => setProfile({ ...profile, preferred_locale: event.target.value })}
          className="atlas-input"
          placeholder="en-GB"
        />
      </Field>
      <Field label="First name">
        <input
          maxLength={80}
          value={profile.first_name ?? ""}
          onChange={(event) => setProfile({ ...profile, first_name: event.target.value || null })}
          className="atlas-input"
        />
      </Field>
      <Field label="Last name">
        <input
          maxLength={80}
          value={profile.last_name ?? ""}
          onChange={(event) => setProfile({ ...profile, last_name: event.target.value || null })}
          className="atlas-input"
        />
      </Field>
      <Field label="Timezone">
        <input
          required
          value={profile.timezone}
          onChange={(event) => setProfile({ ...profile, timezone: event.target.value })}
          className="atlas-input"
          placeholder="Europe/London"
        />
      </Field>
      <Field label="Base currency">
        <input
          required
          minLength={3}
          maxLength={3}
          value={profile.base_currency}
          onChange={(event) =>
            setProfile({ ...profile, base_currency: event.target.value.toUpperCase() })
          }
          className="atlas-input uppercase"
        />
      </Field>
      <Field label="Country of residence">
        <input
          minLength={2}
          maxLength={2}
          value={profile.country_of_residence ?? ""}
          onChange={(event) =>
            setProfile({
              ...profile,
              country_of_residence: event.target.value.toUpperCase() || null,
            })
          }
          className="atlas-input uppercase"
          placeholder="GB"
        />
      </Field>
      <div className="flex items-end">
        <button
          disabled={busy}
          className="rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save profile"}
        </button>
      </div>
      {message ? (
        <p role="status" className="text-sm text-cyan-200 md:col-span-2">
          {message}
        </p>
      ) : null}
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2 text-sm font-medium text-slate-200">
      {label}
      {children}
    </label>
  );
}

function StatusMessage({ message }: { message: string }) {
  return (
    <p
      role="status"
      className="mt-8 rounded-xl border border-white/10 bg-white/5 p-5 text-slate-300"
    >
      {message}
    </p>
  );
}

function toMessage(error: unknown): string {
  if (error instanceof AtlasApiError) {
    if (error.status === 401) return "Your session has expired. Please sign in again.";
    if (error.status === 403) return "You are not authorised to perform this action.";
    return error.requestId ? `${error.message} Request ID: ${error.requestId}` : error.message;
  }
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}
