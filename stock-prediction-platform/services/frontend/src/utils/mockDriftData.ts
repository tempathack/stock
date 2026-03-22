import type {
  DriftEventEntry,
  DriftPageData,
  ActiveModelInfo,
  RollingPerformancePoint,
  RetrainStatus,
  FeatureDistribution,
} from "@/api";

/** Simple seeded PRNG (mulberry32) for deterministic output. */
function seededRandom(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }
  return () => {
    h |= 0;
    h = (h + 0x6d2b79f5) | 0;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function isoDate(daysAgo: number): string {
  const d = new Date("2026-03-22T12:00:00Z");
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString();
}

function buildActiveModel(): ActiveModelInfo {
  return {
    modelName: "CatBoost_standard",
    scalerVariant: "standard",
    version: 3,
    trainedDate: "2026-03-20T08:30:00Z",
    isActive: true,
    oosRmse: 0.0234,
    oosMae: 0.0187,
    oosDirectionalAccuracy: 0.62,
  };
}

function buildDriftEvents(): DriftEventEntry[] {
  return [
    {
      drift_type: "data_drift",
      is_drifted: true,
      severity: "high",
      details: {
        n_features_checked: 27,
        n_features_drifted: 5,
        per_feature: {
          rsi_14: { ks_statistic: 0.18, ks_pvalue: 0.001, psi: 0.35, drifted: true },
          macd_line: { ks_statistic: 0.15, ks_pvalue: 0.003, psi: 0.28, drifted: true },
          bb_upper: { ks_statistic: 0.12, ks_pvalue: 0.012, psi: 0.22, drifted: true },
        },
      },
      timestamp: isoDate(0),
      features_affected: ["rsi_14", "macd_line", "bb_upper", "atr", "rolling_volatility_21"],
    },
    {
      drift_type: "prediction_drift",
      is_drifted: true,
      severity: "medium",
      details: {
        baseline_rmse: 0.022,
        recent_rmse: 0.038,
        threshold: 0.033,
        error_ratio: 1.73,
      },
      timestamp: isoDate(1),
      features_affected: [],
    },
    {
      drift_type: "concept_drift",
      is_drifted: true,
      severity: "high",
      details: {
        historical_rmse: 0.021,
        recent_rmse: 0.035,
        degradation_ratio: 1.67,
        threshold: 1.3,
      },
      timestamp: isoDate(2),
      features_affected: [],
    },
    {
      drift_type: "data_drift",
      is_drifted: true,
      severity: "medium",
      details: {
        n_features_checked: 27,
        n_features_drifted: 3,
        per_feature: {
          rsi_14: { ks_statistic: 0.15, ks_pvalue: 0.003, psi: 0.28, drifted: true },
          sma_20: { ks_statistic: 0.11, ks_pvalue: 0.018, psi: 0.19, drifted: true },
        },
      },
      timestamp: isoDate(4),
      features_affected: ["rsi_14", "sma_20", "atr"],
    },
    {
      drift_type: "data_drift",
      is_drifted: false,
      severity: "low",
      details: {
        n_features_checked: 27,
        n_features_drifted: 1,
        per_feature: {
          rolling_volatility_21: { ks_statistic: 0.09, ks_pvalue: 0.045, psi: 0.12, drifted: true },
        },
      },
      timestamp: isoDate(5),
      features_affected: ["rolling_volatility_21"],
    },
    {
      drift_type: "prediction_drift",
      is_drifted: false,
      severity: "none",
      details: {
        baseline_rmse: 0.022,
        recent_rmse: 0.024,
        threshold: 0.033,
        error_ratio: 1.09,
      },
      timestamp: isoDate(7),
      features_affected: [],
    },
    {
      drift_type: "data_drift",
      is_drifted: true,
      severity: "medium",
      details: {
        n_features_checked: 27,
        n_features_drifted: 4,
        per_feature: {
          macd_line: { ks_statistic: 0.14, ks_pvalue: 0.005, psi: 0.26, drifted: true },
          bb_upper: { ks_statistic: 0.13, ks_pvalue: 0.008, psi: 0.24, drifted: true },
        },
      },
      timestamp: isoDate(9),
      features_affected: ["macd_line", "bb_upper", "sma_20", "ema_12"],
    },
    {
      drift_type: "concept_drift",
      is_drifted: false,
      severity: "low",
      details: {
        historical_rmse: 0.021,
        recent_rmse: 0.026,
        degradation_ratio: 1.24,
        threshold: 1.3,
      },
      timestamp: isoDate(11),
      features_affected: [],
    },
    {
      drift_type: "data_drift",
      is_drifted: false,
      severity: "none",
      details: {
        n_features_checked: 27,
        n_features_drifted: 0,
        per_feature: {},
      },
      timestamp: isoDate(13),
      features_affected: [],
    },
    {
      drift_type: "prediction_drift",
      is_drifted: true,
      severity: "medium",
      details: {
        baseline_rmse: 0.022,
        recent_rmse: 0.034,
        threshold: 0.033,
        error_ratio: 1.55,
      },
      timestamp: isoDate(14),
      features_affected: [],
    },
  ];
}

function buildRollingPerformance(): RollingPerformancePoint[] {
  const rng = seededRandom("rolling_perf_v1");
  const points: RollingPerformancePoint[] = [];

  for (let i = 29; i >= 0; i--) {
    const progress = (29 - i) / 29; // 0→1
    const noise = (rng() - 0.5) * 0.003;
    points.push({
      date: isoDate(i).slice(0, 10),
      rmse: 0.021 + progress * 0.014 + noise,
      mae: 0.017 + progress * 0.011 + (rng() - 0.5) * 0.002,
      directionalAccuracy: 0.63 - progress * 0.08 + (rng() - 0.5) * 0.02,
    });
  }

  return points;
}

function buildRetrainStatus(): RetrainStatus {
  return {
    lastRetrainDate: "2026-03-20T08:30:00Z",
    isRetraining: false,
    oldModel: { name: "Ridge_quantile", rmse: 0.041, mae: 0.033 },
    newModel: { name: "CatBoost_standard", rmse: 0.023, mae: 0.019 },
    improvementPct: 43.9,
  };
}

function buildFeatureDistributions(): FeatureDistribution[] {
  const rng = seededRandom("feat_dist_v1");
  const BIN_LABELS = [
    "0–10",
    "10–20",
    "20–30",
    "30–40",
    "40–50",
    "50–60",
    "60–70",
    "70–80",
    "80–90",
    "90–100",
  ];

  const features: {
    name: string;
    isDrifted: boolean;
    ks: number;
    psi: number;
    shift: number;
  }[] = [
    { name: "rsi_14", isDrifted: true, ks: 0.182, psi: 0.35, shift: 2 },
    { name: "macd_line", isDrifted: true, ks: 0.154, psi: 0.28, shift: 1.5 },
    { name: "bb_upper", isDrifted: true, ks: 0.121, psi: 0.22, shift: 1 },
    { name: "sma_20", isDrifted: false, ks: 0.054, psi: 0.06, shift: 0 },
    { name: "atr", isDrifted: false, ks: 0.042, psi: 0.04, shift: 0 },
    { name: "rolling_volatility_21", isDrifted: false, ks: 0.038, psi: 0.03, shift: 0 },
  ];

  return features.map((f) => {
    // Normal-ish bell for training
    const baseCounts = [8, 18, 35, 55, 70, 68, 52, 30, 15, 6];
    const trainingBins = BIN_LABELS.map((bin, i) => ({
      bin,
      count: (baseCounts[i] ?? 0) + Math.round((rng() - 0.5) * 6),
    }));

    // Shift distribution for drifted features
    const recentBins = BIN_LABELS.map((bin, i) => {
      const shiftIdx = Math.min(9, Math.max(0, Math.round(i + f.shift)));
      const base = baseCounts[shiftIdx] ?? baseCounts[i] ?? 0;
      return { bin, count: base + Math.round((rng() - 0.5) * 8) };
    });

    return {
      feature: f.name,
      trainingBins,
      recentBins,
      ksStat: f.ks,
      psiValue: f.psi,
      isDrifted: f.isDrifted,
    };
  });
}

export function generateMockDriftData(): DriftPageData {
  return {
    activeModel: buildActiveModel(),
    events: buildDriftEvents(),
    rollingPerformance: buildRollingPerformance(),
    retrainStatus: buildRetrainStatus(),
    featureDistributions: buildFeatureDistributions(),
  };
}
