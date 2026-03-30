import { test, expect, request } from "@playwright/test";

// NOTE: No test.describe.configure({ mode: 'serial' }) — these are independent
// stateless API checks and can run in parallel.

const BASE_API_URL = process.env.BASE_API_URL ?? "http://localhost:8000";

// Service availability probe — skip entire file if API unreachable
test.beforeAll(async () => {
  const ctx = await request.newContext({ baseURL: BASE_API_URL });
  try {
    const res = await ctx.get("/health", { timeout: 5_000 });
    if (!res.ok()) {
      test.skip(true, `API not reachable at ${BASE_API_URL}/health (status ${res.status()})`);
    }
  } catch {
    test.skip(true, `API not reachable at ${BASE_API_URL} — ensure port-forward is running`);
  } finally {
    await ctx.dispose();
  }
});

test.describe("Backend API data quality", () => {
  test("GET /health returns status ok", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/health");
      expect(res.status(), `Expected 200 but got ${res.status()}`).toBe(200);
      const body = await res.json();
      // Accept {status: 'ok'}, {status: 'healthy'}, or any object with a status field
      expect(body, "Response body should be an object").toBeTruthy();
      if (body.status !== undefined) {
        expect(
          ["ok", "healthy", "running", "up"].some((s) =>
            String(body.status).toLowerCase().includes(s)
          ),
          `Expected status to indicate healthy, got: ${JSON.stringify(body.status)}`
        ).toBe(true);
      }
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /market/overview returns ≥20 stocks with required fields", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/market/overview");
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      // Accept plain array or wrapped {stocks: [], count: N}
      const stocks: unknown[] = Array.isArray(body) ? body : (body.stocks ?? []);
      expect(Array.isArray(stocks), "Expected an array (or {stocks:[]}  wrapper)").toBe(true);
      expect(
        stocks.length,
        `Expected ≥20 stocks, got ${stocks.length}: ${JSON.stringify(stocks.slice(0, 2))}`
      ).toBeGreaterThanOrEqual(20);

      // Validate first item has required fields
      const first = stocks[0] as Record<string, unknown>;
      expect(first, "First item should be an object").toBeTruthy();
      expect(
        first.ticker ?? first.symbol,
        "Each item must have ticker or symbol"
      ).toBeTruthy();
      expect(
        first.price ?? first.current_price ?? first.close,
        "Each item must have a price field"
      ).not.toBeNull();

      // No null prices in any item
      const nullPriceItems = stocks.filter(
        (item: unknown) => {
          const i = item as Record<string, unknown>;
          return (i.price ?? i.current_price ?? i.close) === null;
        }
      );
      expect(
        nullPriceItems.length,
        `Found ${nullPriceItems.length} items with null price`
      ).toBe(0);
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /predict/bulk?horizon=7 returns ≥10 predictions with real model names", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/predict/bulk?horizon=7", { timeout: 30_000 });
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      // Accept plain array or wrapped {predictions: [], count: N}
      const preds: unknown[] = Array.isArray(body) ? body : (body.predictions ?? []);
      expect(Array.isArray(preds), "Expected an array (or {predictions:[]} wrapper)").toBe(true);
      expect(
        preds.length,
        `Expected ≥10 predictions, got ${preds.length}`
      ).toBeGreaterThanOrEqual(10);

      const first = preds[0] as Record<string, unknown>;
      expect(first.ticker ?? first.symbol, "Each prediction must have ticker").toBeTruthy();
      expect(
        first.predicted_price ?? first.prediction ?? first.predicted_return,
        "Each prediction must have predicted_price"
      ).not.toBeUndefined();

      // model_name must NOT start with 'fixture_'
      const modelName: string = first.model_name ?? first.model ?? "";
      expect(
        modelName.startsWith("fixture_"),
        `model_name starts with 'fixture_': ${modelName}`
      ).toBe(false);
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /predict/AAPL?horizon=7 returns single prediction with confidence metrics", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/predict/AAPL?horizon=7", { timeout: 30_000 });
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      expect(body, "Response should be an object").toBeTruthy();

      const predictedPrice =
        body.predicted_price ?? body.prediction ?? body.predicted_return;
      expect(predictedPrice, "predicted_price should be present").not.toBeUndefined();
      // For price predictions: > 0; for return predictions: any non-null number is fine
      expect(typeof predictedPrice, "predicted_price must be a number").toBe("number");

      // confidence_metrics should be present (object or array)
      const hasConfidence =
        body.confidence_metrics !== undefined ||
        body.confidence !== undefined ||
        body.metrics !== undefined ||
        body.lower_bound !== undefined;
      expect(
        hasConfidence,
        `Expected confidence_metrics or similar field, got keys: ${Object.keys(body).join(", ")}`
      ).toBe(true);
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /models/comparison returns ≥1 model with winner and numeric metrics", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/models/comparison");
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      // Accepts array or {models: [...], winner: ...}
      const models: Record<string, unknown>[] = Array.isArray(body)
        ? body
        : body.models ?? body.results ?? [];
      expect(
        models.length,
        `Expected ≥1 model in comparison, got ${models.length}`
      ).toBeGreaterThanOrEqual(1);

      // Find the winner
      const winner = models.find(
        (m) => m.is_winner === true || m.winner === true || m.rank === 1
      );
      expect(winner ?? models[0], "Should have at least one model entry").toBeTruthy();

      const candidateModel = winner ?? models[0];
      const oos = (candidateModel.oos_metrics as Record<string, unknown>) ?? {};
      const metrics = (candidateModel.metrics as Record<string, unknown>) ?? candidateModel;
      const rmse = oos.oos_rmse ?? metrics.rmse ?? metrics.RMSE ?? candidateModel.rmse;
      const mae = oos.oos_mae ?? metrics.mae ?? metrics.MAE ?? candidateModel.mae;
      expect(typeof rmse, `rmse should be a number, got ${rmse}`).toBe("number");
      expect(typeof mae, `mae should be a number, got ${mae}`).toBe("number");
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /models/drift returns drift_events array and active_model with real name", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/models/drift");
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      expect(body, "Response should be an object").toBeTruthy();

      // drift_events may be empty but must be an array (or present as events)
      const events =
        body.drift_events ?? body.events ?? body.drift_history ?? [];
      expect(
        Array.isArray(events),
        `drift_events should be an array, got: ${typeof events}`
      ).toBe(true);

      // active_model is optional — only validate if present
      const activeModel =
        body.active_model ?? body.current_model ?? body.model;
      if (activeModel) {
        const modelName: string =
          typeof activeModel === "string"
            ? activeModel
            : (activeModel.model_name ?? activeModel.name ?? "");
        expect(
          modelName.startsWith("fixture_"),
          `active_model.model_name starts with 'fixture_': ${modelName}`
        ).toBe(false);
      }
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /market/indicators/AAPL returns rsi, macd_line, sma_20 as numbers", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/market/indicators/AAPL");
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      expect(body, "Response should be an object").toBeTruthy();

      // API returns {latest: {rsi_14, macd_line, sma_20, ...}, series: [...]}
      const latest = body.latest ?? body;
      const rsi = latest.rsi_14 ?? latest.rsi ?? body.rsi ?? body.RSI;
      const macdLine = latest.macd_line ?? latest.macd ?? body.macd_line ?? body.MACD;
      const sma20 = latest.sma_20 ?? latest.sma20 ?? body.sma_20 ?? body.SMA_20;

      expect(typeof rsi, `rsi should be a number, got: ${JSON.stringify(rsi)}`).toBe("number");
      expect(
        typeof macdLine,
        `macd_line should be a number, got: ${JSON.stringify(macdLine)}`
      ).toBe("number");
      expect(
        typeof sma20,
        `sma_20 should be a number, got: ${JSON.stringify(sma20)}`
      ).toBe("number");
    } finally {
      await ctx.dispose();
    }
  });

  test("GET /predict/bulk?horizon=30 returns ≥10 predictions (30-day horizon works)", async () => {
    const ctx = await request.newContext({ baseURL: BASE_API_URL });
    try {
      const res = await ctx.get("/predict/bulk?horizon=30", { timeout: 30_000 });
      expect(
        res.status(),
        `Actual body: ${await res.text()}`
      ).toBe(200);
      const body = await res.json();
      const preds30: unknown[] = Array.isArray(body) ? body : (body.predictions ?? []);
      expect(Array.isArray(preds30), "Expected an array (or {predictions:[]} wrapper)").toBe(true);
      expect(
        preds30.length,
        `Expected ≥10 predictions for 30-day horizon, got ${preds30.length}`
      ).toBeGreaterThanOrEqual(10);
    } finally {
      await ctx.dispose();
    }
  });
});
