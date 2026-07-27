import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import MarketsPage from "@/app/app/markets/page";
import WatchlistsPage from "@/app/app/watchlists/page";
import { MarketDataState } from "@/components/market-data-state";

const getToken = vi.fn(() => Promise.resolve("local-test-token"));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken }),
}));

describe("market-data experience", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    getToken.mockResolvedValue("local-test-token");
  });

  it("shows a prominent simulated-data warning and accessible search", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              total: 1,
              items: [
                {
                  instrument_id: "instrument-1",
                  canonical_name: "Nova Development Equity",
                  short_name: "Nova",
                  asset_class: "equity",
                  status: "active",
                  listing: {
                    id: "listing-1",
                    symbol: "NOVA",
                    currency: "GBP",
                    status: "active",
                    data_availability: "simulated",
                    exchange: { mic: "XDEV", name: "Atlas Development Exchange" },
                  },
                },
              ],
            }),
        }),
      ),
    );
    render(<MarketsPage />);

    expect(screen.getByText(/simulated development data/i)).toBeVisible();
    const search = screen.getByRole("textbox", { name: /search instruments/i });
    fireEvent.change(search, { target: { value: "NOVA" } });
    fireEvent.submit(search.closest("form")!);

    expect(await screen.findByText("Nova Development Equity")).toBeVisible();
    expect(screen.getByText(/1 listing results/i)).toBeVisible();
    expect(screen.queryByText(/\bbuy\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bsell\b/i)).not.toBeInTheDocument();
  });

  it("loads workspace-scoped watchlists without client-authoritative roles", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const body = url.includes("/organisations")
        ? {
            items: [
              {
                id: "tenant-1",
                name: "Personal workspace",
                role: "viewer",
              },
            ],
          }
        : url.includes("/effective-permissions")
          ? { can_create_watchlists: false }
          : [];
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve(body),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<WatchlistsPage />);

    expect(await screen.findByRole("combobox", { name: /workspace/i })).toHaveValue("tenant-1");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(screen.queryByRole("textbox", { name: /watchlist name/i })).not.toBeInTheDocument();
    expect(screen.getByText(/read-only for your account/i)).toBeVisible();
    expect(screen.getByText(/no watchlists in this workspace/i)).toBeVisible();
  });

  it("renders accessible mutation controls only when effective permissions allow them", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const body = url.includes("/organisations")
        ? { items: [{ id: "tenant-1", name: "Owner workspace", role: "owner" }] }
        : url.includes("/effective-permissions")
          ? { can_create_watchlists: true }
          : [];
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve(body),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<WatchlistsPage />);

    const workspace = await screen.findByRole("combobox", { name: /workspace/i });
    const name = await screen.findByRole("textbox", { name: /watchlist name/i });
    const create = screen.getByRole("button", { name: /^create$/i });

    expect(workspace.compareDocumentPosition(name) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(name.compareDocumentPosition(create) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    name.focus();
    expect(name).toHaveFocus();
    create.focus();
    expect(create).toHaveFocus();
  });

  it.each([
    ["simulated", /simulated development data/i],
    ["delayed", /delayed market data/i],
    ["cached", /cached market data/i],
    ["stale", /stale market data/i],
    ["unavailable", /market data unavailable/i],
    ["provider_error", /provider unavailable/i],
    ["rate_limited", /temporarily rate limited/i],
    ["unsupported_interval", /historical interval is unsupported/i],
  ])("renders the %s state without advisory language", (status, expected) => {
    render(<MarketDataState status={status} delaySeconds={60} />);
    expect(screen.getByRole("status")).toHaveTextContent(expected);
    expect(screen.queryByText(/\bbuy\b|\bsell\b/i)).not.toBeInTheDocument();
  });
});
