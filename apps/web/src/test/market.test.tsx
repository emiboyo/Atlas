import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import MarketsPage from "@/app/app/markets/page";
import WatchlistsPage from "@/app/app/watchlists/page";

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
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("textbox", { name: /watchlist name/i })).toBeVisible();
    expect(screen.getByText(/no watchlists in this workspace/i)).toBeVisible();
  });
});
