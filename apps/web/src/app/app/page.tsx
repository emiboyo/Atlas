import Link from "next/link";
import type { Route } from "next";

const cards: { title: string; copy: string; href: Route }[] = [
  {
    title: "Complete your profile",
    copy: "Keep your locale, timezone, and preferred base currency current.",
    href: "/app/profile",
  },
  {
    title: "Manage workspaces",
    copy: "Review your personal workspace and team memberships.",
    href: "/app/organisations",
  },
  {
    title: "Review onboarding",
    copy: "Complete identity setup without implying KYC or investment approval.",
    href: "/app/onboarding",
  },
];

export default function ApplicationHome() {
  return (
    <>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">
        Identity workspace
      </p>
      <h1 className="font-display mt-3 text-4xl font-semibold">Your Atlas account</h1>
      <p className="mt-4 max-w-2xl text-slate-300">
        Manage profile, onboarding, workspaces, and access. No trading or investment functionality
        is enabled.
      </p>
      <div className="mt-10 grid gap-5 md:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-2xl border border-white/10 bg-white/5 p-6 transition hover:border-cyan-300/50"
          >
            <h2 className="font-display text-xl font-semibold">{card.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">{card.copy}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
