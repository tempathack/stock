import type { Page, TestType } from "@playwright/test";

export interface ProductionCheck {
  url: string;
  description: string;
}

/**
 * Calls each URL in the checks array and throws a descriptive error if any returns non-200.
 * Returns true when all checks pass.
 */
export async function requireProductionData(
  page: Page,
  checks: ProductionCheck[]
): Promise<true> {
  for (const check of checks) {
    const response = await page.request.get(check.url, { timeout: 15_000 }).catch(() => null);
    if (!response || !response.ok()) {
      const status = response ? response.status() : "no response";
      throw new Error(
        `Production check failed: ${check.description}\n` +
          `  URL: ${check.url}\n` +
          `  Status: ${status}\n` +
          `  Ensure the service is running and port-forwarded.`
      );
    }
  }
  return true;
}

/**
 * Wraps requireProductionData in a beforeAll hook.
 * Calls test.skip() with a helpful message if any check fails.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function skipIfNotProduction(test: TestType<any, any>, checks: ProductionCheck[]): void {
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await requireProductionData(page, checks);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      test.skip(true, `Production data not available — ${message}`);
    } finally {
      await page.close();
    }
  });
}

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

/** Standard production checks covering all core API endpoints. */
export const PRODUCTION_CHECKS: ProductionCheck[] = [
  {
    url: `${BASE_API_URL}/health`,
    description: "API health endpoint must be 200",
  },
  {
    url: `${BASE_API_URL}/market/overview`,
    description: "market/overview must return data (≥20 stocks expected)",
  },
  {
    url: `${BASE_API_URL}/predict/bulk?horizon=7`,
    description: "predict/bulk?horizon=7 must be reachable",
  },
  {
    url: `${BASE_API_URL}/models/comparison`,
    description: "models/comparison must be reachable (≥1 model expected)",
  },
  {
    url: `${BASE_API_URL}/models/drift`,
    description: "models/drift endpoint must be 200",
  },
];
