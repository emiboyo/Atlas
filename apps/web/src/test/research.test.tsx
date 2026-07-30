import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ResearchPage from "@/app/app/research/page";
import { ResearchScreen } from "@/components/research-screen";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("synthetic-test-token") }),
  UserButton: () => <span data-testid="user-button" />,
}));

const strategy = {
  id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  name: "Evidence strategy",
  description: "Bounded historical hypothesis",
  research_purpose: "Independent historical research",
  status: "active",
  current_version_id: "33333333-3333-4333-8333-333333333333",
  version: 2,
  created_at: "2026-07-29T08:00:00Z",
  updated_at: "2026-07-29T09:00:00Z",
};
const version = {
  id: "33333333-3333-4333-8333-333333333333",
  strategy_id: strategy.id,
  version_number: 1,
  version_label: "SMA evidence",
  configuration_fingerprint: "abc123",
  base_currency: "GBP",
  benchmark_listing_id: null,
  configuration: { listing_id: "44444444-4444-4444-8444-444444444444" },
  created_at: "2026-07-29T08:30:00Z",
};
const run = {
  id: "55555555-5555-4555-8555-555555555555",
  tenant_id: strategy.tenant_id,
  strategy_id: strategy.id,
  strategy_version_id: version.id,
  listing_id: "44444444-4444-4444-8444-444444444444",
  status: "completed",
  configuration_fingerprint: "config",
  data_fingerprint: "data",
  start_date: "2025-01-01",
  end_date: "2025-02-01",
  starting_capital: "10000",
  base_currency: "GBP",
  fee_model: "zero_fee",
  fee_value: "0",
  slippage_model: "zero_slippage",
  slippage_bps: "0",
  execution_policy: "next_open",
  sizing_policy: "fixed_percentage_of_available_simulated_cash",
  sizing_value: "100",
  missing_data_policy: "fail_run",
  engine_version: "atlas-deterministic-v1",
  requested_at: "2026-07-29T09:00:00Z",
  completed_at: "2026-07-29T09:00:01Z",
  failure_code: null,
};
const result = {
  run_id: run.id,
  starting_value: "10000",
  ending_value: "10100",
  simulated_pnl: "100",
  historical_return: "1",
  event_count: 2,
  completed_trade_count: 1,
  maximum_drawdown: "0.5",
  volatility: "2",
  turnover: "200",
  benchmark_return: "0.8",
  missing_count: 0,
  stale_count: 0,
  unavailable_count: 0,
  excluded_count: 0,
  completeness: "complete",
  result_checksum: "checksum",
};
const permissions = {
  can_read: true,
  can_update: true,
  can_archive: true,
  can_create_version: true,
  can_create_backtest: true,
  can_compare: true,
  can_explain: true,
  can_read_audit: true,
};

function response(value: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(status >= 400 ? { error: value } : value), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function requestUrl(input: RequestInfo | URL) {
  return typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
}

function installApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const path = requestUrl(input);
      if (path.endsWith("/organisations"))
        return response({ items: [{ id: strategy.tenant_id, name: "Atlas Lab" }] });
      if (path.includes("/effective-permissions")) return response(permissions);
      if (path.endsWith(`/strategies/${strategy.id}`)) return response(strategy);
      if (path.endsWith(`/strategies/${strategy.id}/versions`)) return response([version]);
      if (path.includes("/research/strategies?")) return response({ items: [strategy] });
      if (path.includes("/research/backtests?")) return response([run]);
      if (path.endsWith(`/backtests/${run.id}`)) return response(run);
      if (path.endsWith(`/backtests/${run.id}/result`)) return response(result);
      if (path.endsWith(`/backtests/${run.id}/data-quality`)) return response(result);
      if (path.endsWith(`/backtests/${run.id}/equity`))
        return response([
          {
            sequence: 1,
            observed_at: "2025-01-01T00:00:00Z",
            total_equity: "10000",
            drawdown_percentage: "0",
          },
        ]);
      if (path.endsWith(`/backtests/${run.id}/events`)) return response([]);
      if (path.endsWith(`/backtests/${run.id}/explanations`)) return response([]);
      if (path.endsWith(`/backtests/${run.id}/audit-events`)) return response([]);
      return response({ code: "not_found", message: "Not found" }, 404);
    }),
  );
}

describe("historical strategy research experience", () => {
  beforeEach(installApi);
  afterEach(() => vi.unstubAllGlobals());

  it("states the governed boundary and exposes no prohibited controls", () => {
    render(<ResearchPage />);
    expect(screen.getByText(/historical simulation only/i)).toBeVisible();
    expect(screen.queryByRole("button", { name: /trade|buy|sell|place order/i })).toBeNull();
    expect(
      screen.queryByText(/recommended strategy|expected return|guaranteed return/i),
    ).toBeNull();
  });

  it("has valid static research navigation without placeholder hrefs", () => {
    render(<ResearchPage />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(3);
    for (const link of links) expect(link.getAttribute("href")).toMatch(/^\/app\/research/);
    expect(document.querySelector('a[href="#"], a[href=""]')).toBeNull();
  });

  it("loads strategy detail and server-derived mutation permissions", async () => {
    render(<ResearchScreen view="overview" strategyId={strategy.id} />);
    expect(await screen.findByRole("heading", { name: strategy.name })).toBeVisible();
    expect(screen.getByRole("button", { name: /archive strategy/i })).toBeVisible();
    expect(screen.getByRole("link", { name: /create immutable version/i })).toHaveAttribute(
      "href",
      `/app/research/strategies/${strategy.id}/versions/new`,
    );
  });

  it("fails closed when effective permissions are malformed", async () => {
    vi.mocked(fetch).mockImplementation((input) => {
      const path = requestUrl(input);
      if (path.includes("/effective-permissions"))
        return response({ ...permissions, can_archive: "true" });
      if (path.endsWith(`/strategies/${strategy.id}`)) return response(strategy);
      return response({ code: "not_found", message: "Not found" }, 404);
    });
    render(<ResearchScreen view="overview" strategyId={strategy.id} />);
    expect(await screen.findByRole("heading", { name: strategy.name })).toBeVisible();
    expect(screen.queryByRole("button", { name: /archive strategy/i })).toBeNull();
    expect(screen.queryByRole("link", { name: /create immutable version/i })).toBeNull();
  });

  it.each([
    [401, "Your session has expired"],
    [403, "do not have permission"],
    [404, "was not found"],
    [503, "temporarily unavailable"],
  ])("handles strategy API status %i safely", async (status, expected) => {
    vi.mocked(fetch).mockImplementation((input) =>
      requestUrl(input).includes("/effective-permissions")
        ? response(permissions)
        : response({ code: "failure", message: "temporarily unavailable" }, status),
    );
    render(<ResearchScreen view="overview" strategyId={strategy.id} />);
    expect(await screen.findByText(new RegExp(expected, "i"))).toBeVisible();
  });

  it("loads version history with immutable dynamic evidence", async () => {
    render(<ResearchScreen view="versions" strategyId={strategy.id} />);
    expect(await screen.findByText(/version 1: sma evidence/i)).toBeVisible();
    expect(screen.getByText(/immutable version id/i)).toBeVisible();
  });

  it("renders supported backtest assumptions and excludes unsupported skip policies", async () => {
    render(<ResearchScreen view="new-run" />);
    expect(
      await screen.findByRole("group", { name: /explicit simulation assumptions/i }),
    ).toBeVisible();
    expect(screen.getByLabelText(/starting simulated capital/i)).toHaveAttribute(
      "inputmode",
      "decimal",
    );
    expect(screen.getByLabelText(/missing-data policy/i)).toBeDisabled();
    expect(screen.queryByText(/skip event|skip observation/i)).toBeNull();
  });

  it("validates typed SMA windows and focuses the status summary", async () => {
    render(<ResearchScreen view="new-version" strategyId={strategy.id} />);
    const form = await screen.findByRole("group", { name: /typed sma crossover rule/i });
    expect(form).toBeVisible();
    fireEvent.change(screen.getByLabelText(/version label/i), { target: { value: "Evidence" } });
    fireEvent.change(screen.getByLabelText(/atlas listing uuid/i), {
      target: { value: "44444444-4444-4444-8444-444444444444" },
    });
    fireEvent.change(screen.getByLabelText(/short window/i), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText(/long window/i), { target: { value: "20" } });
    fireEvent.click(screen.getByRole("button", { name: /save immutable version/i }));
    const status = await screen.findByText(/short window must be less/i);
    await waitFor(() => expect(status).toHaveFocus());
  });

  it("renders API-backed analytics with an accessible table alternative", async () => {
    render(<ResearchScreen view="analytics" runId={run.id} />);
    expect(await screen.findByText(/historical simulated result/i)).toBeVisible();
    expect(
      screen.getByRole("table", { name: /accessible equity and drawdown history/i }),
    ).toBeVisible();
    expect(screen.getByText(/missing 0; stale 0; unavailable 0/i)).toBeVisible();
  });

  it("renders explanation disabled and restricted audit states from permissions", async () => {
    vi.mocked(fetch).mockImplementation((input) => {
      const path = requestUrl(input);
      if (path.includes("/effective-permissions"))
        return response({ ...permissions, can_explain: false, can_read_audit: false });
      if (path.endsWith(`/backtests/${run.id}`)) return response(run);
      if (path.endsWith(`/backtests/${run.id}/explanations`)) return response([]);
      if (path.endsWith(`/backtests/${run.id}/audit-events`)) return response([]);
      return response({});
    });
    const { unmount } = render(<ResearchScreen view="explanations" runId={run.id} />);
    expect(await screen.findByText(/disabled or not permitted/i)).toBeVisible();
    unmount();
    render(<ResearchScreen view="audit" runId={run.id} />);
    expect(await screen.findByText(/restricted to authorised users/i)).toBeVisible();
  });

  it("creates dynamic run navigation links without dead controls", async () => {
    render(<ResearchScreen view="run" runId={run.id} />);
    expect(await screen.findByText(/historical simulated result/i)).toBeVisible();
    expect(screen.getByRole("link", { name: "Events" })).toHaveAttribute(
      "href",
      `/app/research/backtests/${run.id}/events`,
    );
    expect(document.querySelector('button[type="button"]:not([disabled])')).toBeNull();
  });

  it.each([
    ["overview", strategy.id, undefined],
    ["versions", strategy.id, undefined],
    ["new-version", strategy.id, undefined],
    ["runs", undefined, undefined],
    ["new-run", undefined, undefined],
    ["run", undefined, run.id],
    ["events", undefined, run.id],
    ["analytics", undefined, run.id],
    ["explanations", undefined, run.id],
    ["audit", undefined, run.id],
    ["compare", undefined, undefined],
  ] as const)(
    "has no serious or critical automated accessibility violations in %s",
    async (view, strategyId, runId) => {
      const { container } = render(
        <ResearchScreen view={view} strategyId={strategyId} runId={runId} />,
      );
      await waitFor(() => expect(fetch).toHaveBeenCalled());
      const scan = await axe.run(container, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
        rules: { "color-contrast": { enabled: false } },
      });
      expect(
        scan.violations.filter(({ impact }) => impact === "serious" || impact === "critical"),
      ).toEqual([]);
    },
  );

  it("has no serious or critical automated accessibility violations on the research landing page", async () => {
    const { container } = render(<ResearchPage />);
    const scan = await axe.run(container, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      rules: { "color-contrast": { enabled: false } },
    });
    expect(
      scan.violations.filter(({ impact }) => impact === "serious" || impact === "critical"),
    ).toEqual([]);
  });
});
