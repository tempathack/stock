import type {
  ShapFeatureImportance,
  ShapBeeswarmPoint,
  FoldMetric,
  ModelDetailData,
} from "@/api";

const FEATURE_NAMES = [
  "rsi_14",
  "macd_line",
  "macd_signal",
  "sma_20",
  "sma_50",
  "sma_200",
  "ema_12",
  "ema_26",
  "bb_upper",
  "bb_lower",
  "atr",
  "obv",
  "volume_sma_20",
  "return_1d",
  "return_5d",
  "return_21d",
  "rolling_vol_21",
  "close_lag_1",
  "close_lag_5",
  "close_lag_21",
];

/** Simple seeded PRNG (mulberry32) for deterministic output per model name. */
function seededRandom(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(31, h) + seed.charCodeAt(i) | 0;
  }
  return () => {
    h |= 0;
    h = (h + 0x6d2b79f5) | 0;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function generateMockShapImportance(modelName: string): ShapFeatureImportance[] {
  const rng = seededRandom(modelName);
  return FEATURE_NAMES.map((feature) => ({
    feature,
    importance: 0.001 + rng() * 0.149,
  }))
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 15);
}

export function generateMockBeeswarm(modelName: string): ShapBeeswarmPoint[] {
  const rng = seededRandom(modelName + "_beeswarm");
  const importance = generateMockShapImportance(modelName);
  const points: ShapBeeswarmPoint[] = [];

  for (const feat of importance) {
    const spread = feat.importance * 2;
    for (let s = 0; s < 12; s++) {
      points.push({
        feature: feat.feature,
        feature_value: rng(),
        shap_value: (rng() - 0.5) * spread,
      });
    }
  }

  return points;
}

export function generateMockFoldMetrics(modelName: string): FoldMetric[] {
  const rng = seededRandom(modelName + "_folds");
  const baseRmse = 0.01 + rng() * 0.04;
  const baseMae = baseRmse * (0.6 + rng() * 0.3);
  const baseR2 = 0.7 + rng() * 0.25;

  return Array.from({ length: 5 }, (_, i) => ({
    fold: i + 1,
    rmse: baseRmse + (rng() - 0.5) * 0.005,
    mae: baseMae + (rng() - 0.5) * 0.003,
    r2: Math.min(0.99, Math.max(0.3, baseR2 + (rng() - 0.5) * 0.08)),
  }));
}

export function generateModelDetail(modelName: string): ModelDetailData {
  return {
    model_name: modelName,
    shap_importance: generateMockShapImportance(modelName),
    shap_beeswarm: generateMockBeeswarm(modelName),
    fold_metrics: generateMockFoldMetrics(modelName),
  };
}
