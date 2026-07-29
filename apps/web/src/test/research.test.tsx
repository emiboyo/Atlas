import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ResearchPage from "@/app/app/research/page";
import { ResearchScreen } from "@/components/research-screen";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("synthetic-test-token") }),
  UserButton: () => <span data-testid="user-button" />,
}));

describe("historical strategy research experience", () => {
  it("states the governed boundary and exposes no execution controls", () => {
    render(<ResearchPage />);
    expect(screen.getByText(/historical simulation only/i)).toBeVisible();
    expect(
      screen.getByText(/cannot place orders, connect to a broker, or move money/i),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /trade|buy|sell|place order|connect broker/i }),
    ).toBeNull();
    expect(screen.queryByText(/recommended|expected return|guaranteed/i)).toBeNull();
  });

  it("renders accessible explicit assumptions and typed bounded rule fields", () => {
    const { rerender } = render(<ResearchScreen view="new-run" />);
    expect(screen.getByRole("group", { name: /explicit simulation assumptions/i })).toBeVisible();
    expect(screen.getByLabelText(/starting virtual capital/i)).toHaveAttribute(
      "inputmode",
      "decimal",
    );
    expect(screen.getByLabelText(/missing-data policy/i)).toBeVisible();
    rerender(<ResearchScreen view="new-version" strategyId="strategy-1" />);
    expect(screen.getByRole("group", { name: /sma crossover rule/i })).toBeVisible();
    expect(screen.getByLabelText(/short window/i)).toHaveAttribute("max", "100");
    expect(screen.getByLabelText(/long window/i)).toHaveAttribute("max", "250");
  });

  it("provides non-visual analytics, quality, explanation, and audit states", () => {
    const { rerender } = render(<ResearchScreen view="analytics" runId="run-1" />);
    expect(screen.getByText(/text alternative: equity, peak, and drawdown/i)).toBeVisible();
    expect(screen.getByText(/data quality · unavailable/i)).toBeVisible();
    expect(screen.getByText(/descriptive benchmark comparison/i)).toBeVisible();
    rerender(<ResearchScreen view="explanations" runId="run-1" />);
    expect(screen.getByText(/explanations are disabled safely/i)).toBeVisible();
    expect(screen.getByText(/no advice, suitability assessment/i)).toBeVisible();
    rerender(<ResearchScreen view="audit" runId="run-1" />);
    expect(screen.getByText(/append-only evidence/i)).toBeVisible();
  });
});
