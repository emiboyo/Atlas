"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import type { Route } from "next";
import { ThemeToggle } from "@/components/theme-toggle";

const links: { href: Route; label: string }[] = [
  { href: "/app", label: "Overview" },
  { href: "/app/onboarding", label: "Onboarding" },
  { href: "/app/profile", label: "Profile" },
  { href: "/app/organisations", label: "Workspaces" },
  { href: "/app/markets", label: "Markets" },
  { href: "/app/watchlists", label: "Watchlists" },
  { href: "/app/portfolios", label: "Portfolios" },
  { href: "/app/research", label: "Research" },
];

export function AccountNavigation() {
  return (
    <header className="border-b border-white/10 bg-slate-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
        <Link href="/app" className="font-display text-xl font-semibold text-white">
          Atlas AI
        </Link>
        <nav aria-label="Application navigation" className="hidden gap-5 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-slate-300 hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserButton afterSignOutUrl="/" />
        </div>
      </div>
      <nav
        aria-label="Mobile application navigation"
        className="flex gap-4 overflow-x-auto px-4 pb-3 md:hidden"
      >
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="whitespace-nowrap text-sm text-slate-300"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
