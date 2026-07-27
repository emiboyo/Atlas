import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import type { Route } from "next";
import { AccountNavigation } from "@/components/account-navigation";

export default async function ProtectedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-950 p-6 text-white">
        <section className="max-w-lg rounded-2xl border border-amber-400/30 bg-amber-400/10 p-8">
          <h1 className="font-display text-2xl font-semibold">Protected access unavailable</h1>
          <p className="mt-3 text-slate-300">
            Clerk is not configured. Atlas fails closed and has not granted a development bypass.
          </p>
        </section>
      </main>
    );
  }
  const { userId } = await auth();
  if (!userId) {
    redirect("/sign-in" as Route);
  }
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <AccountNavigation />
      <main className="mx-auto max-w-7xl px-4 py-10">{children}</main>
    </div>
  );
}
