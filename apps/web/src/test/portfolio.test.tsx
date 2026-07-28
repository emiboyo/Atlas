import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PortfoliosPage from "@/app/app/portfolios/page";
import { PortfolioTransactionForm } from "@/components/portfolio-transaction-form";
import { PortfolioWorkspace } from "@/components/portfolio-workspace";

const getToken = vi.fn(() => Promise.resolve("synthetic-test-token"));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken }),
  UserButton: () => <span data-testid="user-button" />,
}));

function response(body: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(),
    json: () => Promise.resolve(body),
  });
}

const portfolio = {
  id: "portfolio-1",
  name: "Development portfolio",
  description: "Paper accounting only",
  base_currency: "GBP",
  status: "active",
  version: 1,
};

describe("simulated portfolio experience", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    getToken.mockResolvedValue("synthetic-test-token");
  });

  it("lists workspace-scoped simulated portfolios with accessible creation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        return url.includes("/organisations")
          ? response({ items: [{ id: "tenant-1", name: "Private workspace", role: "member" }] })
          : response({ items: [portfolio] });
      }),
    );
    render(<PortfoliosPage />);

    expect(screen.getByText(/no real money or orders/i)).toBeVisible();
    expect(await screen.findByText("Development portfolio")).toBeVisible();
    expect(screen.getByRole("combobox", { name: /workspace/i })).toHaveValue("tenant-1");
    expect(screen.getByRole("link", { name: /create simulated portfolio/i })).toBeVisible();
    expect(screen.queryByText(/recommended allocation|expected gain|safe investment/i)).toBeNull();
  });

  it("renders a viewer-safe read-only portfolio with explicit stale and missing states", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        if (url.endsWith("/effective-permissions")) {
          return response({
            can_update: false,
            can_archive: false,
            can_create_transaction: false,
            can_read_audit: false,
          });
        }
        if (url.endsWith("/valuation")) {
          return response({
            base_currency: "GBP",
            base_currency_total: null,
            completeness: "incomplete",
            virtual_cash_by_currency: [{ currency: "GBP", amount: "100.00" }],
            positions: [
              {
                listing_id: "listing-1",
                symbol: "NOVA",
                exchange: "XDEV",
                currency: "GBP",
                quantity: "1",
                average_cost_per_unit: "10",
                cost_basis: "10",
                realised_simulated_pnl: "0",
                position_status: "open",
                market_value: null,
                unrealised_simulated_pnl: null,
                data_status: "unavailable",
                valuation_status: "missing",
              },
            ],
            unconverted_currencies: ["USD"],
            missing_listing_ids: ["listing-1"],
            stale_listing_ids: ["listing-2"],
          });
        }
        return response(portfolio);
      }),
    );
    render(<PortfolioWorkspace portfolioId="portfolio-1" />);

    expect(await screen.findByText(/unavailable \/ incomplete/i)).toBeVisible();
    expect(screen.getByText(/1 missing prices/i)).toBeVisible();
    expect(screen.getByText(/unconverted: usd/i)).toBeVisible();
    expect(screen.getAllByText(/missing/i).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /archive/i })).toBeNull();
    expect(screen.queryByText(/^audit history$/i)).toBeNull();
  });

  it("keeps viewer transaction history read-only", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        if (url.endsWith("/effective-permissions")) {
          return response({
            can_update: false,
            can_archive: false,
            can_create_transaction: false,
            can_read_audit: false,
          });
        }
        if (url.endsWith("/transactions")) return response({ items: [] });
        return response(portfolio);
      }),
    );
    render(<PortfolioWorkspace portfolioId="portfolio-1" view="transactions" />);

    expect(await screen.findByText(/no simulated transactions yet/i)).toBeVisible();
    expect(screen.queryByRole("link", { name: /record simulated activity/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /reversal/i })).toBeNull();
  });

  it("uses explicit paper-accounting language and accessible decimal inputs", () => {
    render(<PortfolioTransactionForm portfolioId="portfolio-1" />);

    expect(screen.getByText(/cannot contact a broker, bank, exchange/i)).toBeVisible();
    const type = screen.getByRole("combobox", { name: /simulated transaction type/i });
    fireEvent.change(type, { target: { value: "simulated_buy" } });
    expect(screen.getByRole("option", { name: /record virtual deposit/i })).toBeVisible();
    expect(screen.getByRole("textbox", { name: /simulated quantity/i })).toHaveAttribute(
      "inputmode",
      "decimal",
    );
    expect(screen.getByRole("button", { name: /record simulated buy/i })).toBeVisible();
    expect(
      screen.queryByText(/buy now|sell now|place order|connect broker|connect bank/i),
    ).toBeNull();
  });

  it("shows descriptive analytics and a chart text alternative without recommendations", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        if (url.endsWith("/effective-permissions")) {
          return response({
            can_update: true,
            can_archive: true,
            can_create_transaction: true,
            can_read_audit: true,
          });
        }
        if (url.endsWith("/analytics")) {
          return response({
            allocation: [{ label: "NOVA · XDEV", currency: "GBP", value: "80", percentage: "80" }],
            realised_simulated_pnl: "5",
            unrealised_simulated_pnl: null,
            currency_exposure: { GBP: "100" },
            data_complete: false,
            disclaimer: "Simulated and informational only. This is not investment advice.",
          });
        }
        return response(portfolio);
      }),
    );
    render(<PortfolioWorkspace portfolioId="portfolio-1" view="analytics" />);

    expect(await screen.findByText(/text alternative: allocation values/i)).toBeVisible();
    expect(screen.getAllByText(/not investment advice/i)).toHaveLength(2);
    expect(screen.getByText(/unavailable when valuation data is incomplete/i)).toBeVisible();
    await waitFor(() =>
      expect(screen.queryByText(/recommended|best investment|expected return/i)).toBeNull(),
    );
  });
});
