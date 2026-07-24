"use client";

import { Button } from "@atlas/ui/button";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="max-w-md text-center">
        <p className="text-primary text-sm font-semibold">Something went wrong</p>
        <h1 className="font-display mt-3 text-3xl font-semibold">
          We could not load this experience.
        </h1>
        <p className="text-muted-foreground mt-4">The issue has been recorded. Please try again.</p>
        <Button className="mt-7" onClick={reset}>
          Try again
        </Button>
      </div>
    </main>
  );
}
