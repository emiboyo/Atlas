import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return <ProviderUnavailable title="Sign in" />;
  }
  return (
    <main className="grid min-h-screen place-items-center bg-slate-950 p-6">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" forceRedirectUrl="/app" />
    </main>
  );
}

function ProviderUnavailable({ title }: { title: string }) {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-950 p-6 text-white">
      <section className="max-w-md rounded-2xl border border-amber-400/30 bg-amber-400/10 p-8">
        <h1 className="font-display text-2xl font-semibold">{title} unavailable</h1>
        <p className="mt-3 text-slate-300">
          Authentication is not configured in this environment. Protected access remains closed.
        </p>
      </section>
    </main>
  );
}
