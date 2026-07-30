import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const strategyId = "11111111-1111-4111-8111-111111111111";
const runId = "55555555-5555-4555-8555-555555555555";
const routes = [
  "/app/research",
  "/app/research/strategies",
  "/app/research/strategies/new",
  `/app/research/strategies/${strategyId}`,
  `/app/research/strategies/${strategyId}/versions/new`,
  "/app/research/backtests",
  "/app/research/backtests/new",
  `/app/research/backtests/${runId}`,
  `/app/research/backtests/${runId}/events`,
  `/app/research/backtests/${runId}/analytics`,
  `/app/research/backtests/${runId}/explanations`,
  `/app/research/backtests/${runId}/audit`,
  "/app/research/compare",
] as const;

for (const route of routes) {
  test(`${route} passes focused browser accessibility evidence`, async ({ page }) => {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByText(/historical simulation only/i).first()).toBeVisible();
    await expect(
      page.getByRole("button", { name: /trade|broker|buy|sell|recommend|execute/i }),
    ).toHaveCount(0);
    await expect(page.locator('[role="button"]:not(button)')).toHaveCount(0);

    const seriousOrCritical = (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze()
    ).violations.filter(({ impact }) => impact === "serious" || impact === "critical");
    expect(seriousOrCritical).toEqual([]);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow).toBe(false);

    const interactive = page.locator("a[href], button:not([disabled]), input, select, textarea");
    if ((await interactive.count()) > 0) {
      await page.keyboard.press("Tab");
      await expect(page.locator(":focus")).toBeVisible();
      const focusStyle = await page.locator(":focus").evaluate((element) => {
        const style = getComputedStyle(element);
        return {
          outline: style.outlineStyle,
          outlineWidth: style.outlineWidth,
          boxShadow: style.boxShadow,
        };
      });
      expect(
        focusStyle.outline !== "none" ||
          focusStyle.outlineWidth !== "0px" ||
          focusStyle.boxShadow !== "none",
      ).toBe(true);
    }
  });
}

test("links activate with Enter in Chromium", async ({ page }) => {
  await page.goto("/app/research");
  const strategies = page.getByRole("link", { name: /strategies/i });
  await strategies.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/app\/research\/strategies$/);
});

test("version validation summary receives real browser focus", async ({ page }) => {
  await page.goto(`/app/research/strategies/${strategyId}/versions/new`);
  await page.getByLabel(/version label/i).fill("Browser evidence");
  await page.getByLabel(/atlas listing uuid/i).fill("44444444-4444-4444-8444-444444444444");
  await page.getByLabel(/short window/i).fill("50");
  await page.getByLabel(/long window/i).fill("20");
  await page.getByRole("button", { name: /save immutable version/i }).press("Space");
  await expect(page.getByText(/short window must be less/i)).toBeFocused();
});

test("axe negative control detects an unnamed button and unlabelled input", async ({ page }) => {
  await page.setContent("<main><button></button><input /></main>");
  const ruleIds = (await new AxeBuilder({ page }).analyze()).violations.map(({ id }) => id);
  expect(ruleIds).toContain("button-name");
  expect(ruleIds).toContain("label");
});
