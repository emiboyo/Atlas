import { Button } from "@atlas/ui/button";
import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="text-center">
        <p className="text-primary font-mono text-sm">404</p>
        <h1 className="font-display mt-3 text-4xl font-semibold">Page not found</h1>
        <p className="text-muted-foreground mt-4">The page you requested does not exist.</p>
        <Button className="mt-7" asChild>
          <Link href="/">Return home</Link>
        </Button>
      </div>
    </main>
  );
}
