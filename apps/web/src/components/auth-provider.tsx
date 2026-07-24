import { ClerkProvider } from "@clerk/nextjs";

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey || publishableKey.includes("replace_me")) {
    return children;
  }

  return <ClerkProvider publishableKey={publishableKey}>{children}</ClerkProvider>;
}
