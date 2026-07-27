import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ApplicationHome from "@/app/app/page";
import ProtectedLayout from "@/app/app/layout";
import SignInPage from "@/app/sign-in/[[...sign-in]]/page";
import SignUpPage from "@/app/sign-up/[[...sign-up]]/page";

describe("identity experience", () => {
  it("fails closed when Clerk is not configured", async () => {
    const previous = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

    render(await ProtectedLayout({ children: <p>Protected content</p> }));

    expect(screen.getByRole("heading", { name: /protected access unavailable/i })).toBeVisible();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = previous;
  });

  it("renders stable unavailable sign-in and registration states without a bypass", () => {
    const previous = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

    const signIn = render(<SignInPage />);
    expect(screen.getByRole("heading", { name: /sign in unavailable/i })).toBeVisible();
    signIn.unmount();
    render(<SignUpPage />);
    expect(screen.getByRole("heading", { name: /registration unavailable/i })).toBeVisible();
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = previous;
  });

  it("keeps the protected dashboard identity-only", () => {
    render(<ApplicationHome />);

    expect(screen.getByRole("heading", { name: /your atlas account/i })).toBeVisible();
    expect(screen.getByText(/no trading or investment functionality is enabled/i)).toBeVisible();
    expect(screen.getAllByRole("link")).toHaveLength(3);
  });
});
