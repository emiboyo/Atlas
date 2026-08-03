import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import HomePage from "../app/page";

const clerkState = vi.hoisted(() => ({ signedIn: false }));

vi.mock("@clerk/nextjs", () => ({
  SignedIn: ({ children }: { children: React.ReactNode }) =>
    clerkState.signedIn ? children : null,
  SignedOut: ({ children }: { children: React.ReactNode }) =>
    clerkState.signedIn ? null : children,
  UserButton: ({ afterSignOutUrl }: { afterSignOutUrl: string }) => (
    <button type="button" data-after-sign-out-url={afterSignOutUrl}>
      Account menu
    </button>
  ),
}));

describe("HomePage", () => {
  beforeEach(() => {
    clerkState.signedIn = false;
  });

  it("presents the Atlas AI positioning", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /the intelligent investment operating system/i }),
    ).toBeInTheDocument();
  });

  it("only renders valid internal navigation targets", () => {
    const { container } = render(<HomePage />);
    const targets = Array.from(container.querySelectorAll("a")).map((link) =>
      link.getAttribute("href"),
    );

    expect(targets).not.toContain("#");
    expect(targets).toEqual(expect.arrayContaining(["/", "/sign-in", "/sign-up"]));
  });

  it("shows clear, accessible signed-out authentication entry points", () => {
    render(<HomePage />);

    const signIn = screen.getByRole("link", { name: "Sign in" });
    const getStarted = screen.getByRole("link", { name: "Get started" });
    const createAccount = screen.getByRole("link", { name: /create account/i });

    expect(signIn).toHaveAttribute("href", "/sign-in");
    expect(getStarted).toHaveAttribute("href", "/sign-up");
    expect(createAccount).toHaveAttribute("href", "/sign-up");
    expect(screen.queryByRole("link", { name: /open dashboard/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /account menu/i })).not.toBeInTheDocument();

    signIn.focus();
    expect(signIn).toHaveFocus();
    expect(signIn.closest("nav")).toHaveAttribute("aria-label", "Primary navigation");
  });

  it("shows only dashboard entry and account controls when signed in", () => {
    clerkState.signedIn = true;
    render(<HomePage />);

    const dashboardLinks = screen.getAllByRole("link", { name: /open.*dashboard/i });
    expect(dashboardLinks).toHaveLength(2);
    dashboardLinks.forEach((link) => expect(link).toHaveAttribute("href", "/app"));
    expect(screen.getByRole("button", { name: /account menu/i })).toHaveAttribute(
      "data-after-sign-out-url",
      "/",
    );
    expect(screen.queryByRole("link", { name: "Sign in" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /create account|get started/i }),
    ).not.toBeInTheDocument();

    dashboardLinks[0]?.focus();
    expect(dashboardLinks[0]).toHaveFocus();
  });

  it("uses historical-research copy without implying current investing or execution", () => {
    render(<HomePage />);

    expect(screen.getAllByText(/transparent historical simulations/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/not investment advice.*not a guarantee/i)).toBeInTheDocument();
    expect(screen.queryByText(/first \$10|invest with confidence/i)).not.toBeInTheDocument();
  });
});
