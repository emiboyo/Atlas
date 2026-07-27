"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import { atlasApi } from "@/lib/api-client";

type Organisation = {
  id: string;
  name: string;
  slug: string;
  organisation_type: string;
  status: string;
  role: "owner" | "admin" | "member" | "viewer";
};

type Membership = {
  id: string;
  user_id: string;
  role: string;
  status: string;
};

export function OrganisationPanel({ organisationId }: { organisationId: string }) {
  const { getToken } = useAuth();
  const [organisation, setOrganisation] = useState<Organisation | null>(null);
  const [members, setMembers] = useState<Membership[]>([]);
  const [message, setMessage] = useState("Loading workspace…");
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("member");

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication is required.");
        const current = await atlasApi<Organisation>(`/organisations/${organisationId}`, token);
        let membershipItems: Membership[] = [];
        if (current.role !== "viewer") {
          const page = await atlasApi<{ items: Membership[] }>(
            `/organisations/${organisationId}/members`,
            token,
          );
          membershipItems = page.items;
        }
        if (active) {
          setOrganisation(current);
          setMembers(membershipItems);
          setMessage("");
        }
      } catch (error) {
        if (active) {
          setMessage(error instanceof Error ? error.message : "Workspace access was denied.");
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [getToken, organisationId]);

  async function addMember(event: FormEvent) {
    event.preventDefault();
    if (!organisation) return;
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication is required.");
      const membership = await atlasApi<Membership>(
        `/organisations/${organisationId}/members`,
        token,
        { method: "POST", body: JSON.stringify({ user_id: userId, role }) },
      );
      setMembers([...members, membership]);
      setUserId("");
      setMessage("Member added.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The member could not be added.");
    }
  }

  if (!organisation) {
    return (
      <p role="status" className="mt-8 text-slate-300">
        {message}
      </p>
    );
  }
  const canManage = organisation.role === "owner" || organisation.role === "admin";

  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section>
        <h2 className="font-display text-2xl font-semibold">{organisation.name}</h2>
        <p className="mt-2 text-sm text-slate-400">
          {organisation.organisation_type} · {organisation.role} · {organisation.status}
        </p>
        <h3 className="mt-8 font-semibold">Memberships</h3>
        <div className="mt-3 grid gap-2">
          {members.map((membership) => (
            <div key={membership.id} className="rounded-lg border border-white/10 p-4 text-sm">
              <span className="break-all text-slate-300">{membership.user_id}</span>
              <span className="ml-3 text-cyan-300">{membership.role}</span>
            </div>
          ))}
          {!members.length ? (
            <p className="text-sm text-slate-400">No visible memberships.</p>
          ) : null}
        </div>
      </section>
      {canManage ? (
        <form
          onSubmit={(event) => void addMember(event)}
          className="rounded-2xl border border-white/10 bg-white/5 p-6"
        >
          <h2 className="font-display text-xl font-semibold">Add an existing Atlas user</h2>
          <p className="mt-2 text-sm text-slate-400">
            Email invitations are intentionally not implemented. Use an immutable Atlas user ID.
          </p>
          <label className="mt-5 grid gap-2 text-sm">
            Atlas user ID
            <input
              required
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              className="atlas-input"
            />
          </label>
          <label className="mt-4 grid gap-2 text-sm">
            Role
            <select
              value={role}
              onChange={(event) => setRole(event.target.value)}
              className="atlas-input"
            >
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button className="mt-5 rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950">
            Add member
          </button>
        </form>
      ) : (
        <p className="rounded-xl border border-white/10 bg-white/5 p-5 text-sm text-slate-400">
          Your role has read-only workspace access.
        </p>
      )}
      {message ? (
        <p role="status" className="text-sm text-cyan-200 lg:col-span-2">
          {message}
        </p>
      ) : null}
    </div>
  );
}
