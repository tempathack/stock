"""Hyperparameter search spaces and model family configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.ensemble import (
    AdaBoostRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import (
    BayesianRidge,
    ElasticNet,
    Lasso,
    LinearRegression,
    Ridge,
)
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ModelConfig:
    """Configuration for a single sklearn regressor."""

    name: str
    model_class: type
    default_params: dict[str, Any] = field(default_factory=dict)
    search_space: dict[str, Any] | None = None
    n_iter: int = 30


@dataclass
class TrainingResult:
    """Outcome of a single (model × scaler) training run."""

    model_name: str
    scaler_variant: str
    best_params: dict[str, Any]
    fold_metrics: list[dict[str, float]]
    oos_metrics: dict[str, float]
    fold_stability: float
    pipeline_path: str | None = None

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "model_name": self.model_name,
            "scaler_variant": self.scaler_variant,
            "best_params": self.best_params,
            "fold_metrics": self.fold_metrics,
            "oos_metrics": self.oos_metrics,
            "fold_stability": self.fold_stability,
            "pipeline_path": self.pipeline_path,
        }


# ---------------------------------------------------------------------------
# Linear model family (Phase 12)
# ---------------------------------------------------------------------------

LINEAR_MODELS: dict[str, ModelConfig] = {
    "linear_regression": ModelConfig(
        name="linear_regression",
        model_class=LinearRegression,
    ),
    "ridge": ModelConfig(
        name="ridge",
        model_class=Ridge,
        search_space={"alpha": np.logspace(-3, 3, 50).tolist()},
    ),
    "lasso": ModelConfig(
        name="lasso",
        model_class=Lasso,
        default_params={"max_iter": 10_000},
        search_space={"alpha": np.logspace(-4, 1, 50).tolist()},
    ),
    "elastic_net": ModelConfig(
        name="elastic_net",
        model_class=ElasticNet,
        default_params={"max_iter": 10_000},
        search_space={
            "alpha": np.logspace(-4, 1, 30).tolist(),
            "l1_ratio": np.linspace(0.1, 0.9, 9).tolist(),
        },
    ),
    "bayesian_ridge": ModelConfig(
        name="bayesian_ridge",
        model_class=BayesianRidge,
    ),
}


# ---------------------------------------------------------------------------
# Tree-based model family (Phase 13)
# ---------------------------------------------------------------------------

TREE_MODELS: dict[str, ModelConfig] = {
    "random_forest": ModelConfig(
        name="random_forest",
        model_class=RandomForestRegressor,
        default_params={"random_state": 42, "n_jobs": 1},
        search_space={
            "n_estimators": [50, 100, 200, 300],
            "max_depth": [5, 10, 15, 20, None],
            "min_samples_split": [2, 5, 10],
            "max_features": ["sqrt", "log2", 0.5, 0.8],
        },
        n_iter=50,
    ),
    "gradient_boosting": ModelConfig(
        name="gradient_boosting",
        model_class=GradientBoostingRegressor,
        default_params={"random_state": 42},
        search_space={
            "n_estimators": [100, 200, 300],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "max_depth": [3, 5, 7],
            "subsample": [0.7, 0.8, 0.9, 1.0],
        },
        n_iter=50,
    ),
    "hist_gradient_boosting": ModelConfig(
        name="hist_gradient_boosting",
        model_class=HistGradientBoostingRegressor,
        default_params={"random_state": 42},
        search_space={
            "learning_rate": [0.01, 0.05, 0.1],
            "max_iter": [100, 200, 300],
            "max_depth": [3, 5, 7, None],
        },
    ),
    "extra_trees": ModelConfig(
        name="extra_trees",
        model_class=ExtraTreesRegressor,
        default_params={"random_state": 42, "n_jobs": 1},
        search_space={
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 15, 20, None],
        },
    ),
    "decision_tree": ModelConfig(
        name="decision_tree",
        model_class=DecisionTreeRegressor,
        default_params={"random_state": 42},
        search_space={
            "max_depth": [3, 5, 7, 10, 15, None],
            "min_samples_split": [2, 5, 10, 20],
        },
    ),
    "adaboost": ModelConfig(
        name="adaboost",
        model_class=AdaBoostRegressor,
        default_params={"random_state": 42},
        search_space={
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1, 0.5, 1.0],
        },
    ),
}


# ---------------------------------------------------------------------------
# Optional booster models (Phase 13) — conditional imports
# ---------------------------------------------------------------------------

BOOSTER_MODELS: dict[str, ModelConfig] = {}

try:
    from xgboost import XGBRegressor

    BOOSTER_MODELS["xgboost"] = ModelConfig(
        name="xgboost",
        model_class=XGBRegressor,
        default_params={"random_state": 42, "verbosity": 0, "n_jobs": 1},
        search_space={
            "n_estimators": [100, 200, 300],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "max_depth": [3, 5, 7],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.6, 0.8, 1.0],
        },
        n_iter=50,
    )
except ImportError:
    pass

try:
    from lightgbm import LGBMRegressor

    BOOSTER_MODELS["lightgbm"] = ModelConfig(
        name="lightgbm",
        model_class=LGBMRegressor,
        default_params={"random_state": 42, "verbose": -1, "n_jobs": 1},
        search_space={
            "n_estimators": [100, 200, 300],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "num_leaves": [15, 31, 63, 127],
            "max_depth": [3, 5, 7, -1],
        },
        n_iter=50,
    )
except ImportError:
    pass

try:
    from catboost import CatBoostRegressor

    BOOSTER_MODELS["catboost"] = ModelConfig(
        name="catboost",
        model_class=CatBoostRegressor,
        default_params={"random_seed": 42, "verbose": 0, "train_dir": "/tmp/catboost_info"},
        search_space={
            "iterations": [100, 200, 300],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "depth": [4, 6, 8, 10],
        },
    )
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Distance, SVM & Neural model family (Phase 14)
# ---------------------------------------------------------------------------

DISTANCE_NEURAL_MODELS: dict[str, ModelConfig] = {
    "knn": ModelConfig(
        name="knn",
        model_class=KNeighborsRegressor,
        search_space={
            "n_neighbors": [3, 5, 7, 9, 11, 15, 21],
            "weights": ["uniform", "distance"],
            "metric": ["euclidean", "manhattan"],
        },
        n_iter=30,
    ),
    "svr": ModelConfig(
        name="svr",
        model_class=SVR,
        default_params={"kernel": "rbf"},
        search_space={
            "C": np.logspace(-2, 2, 10).tolist(),
            "gamma": ["scale", "auto", 0.001, 0.01, 0.1],
            "epsilon": np.linspace(0.01, 0.5, 10).tolist(),
        },
        n_iter=30,
    ),
    "mlp": ModelConfig(
        name="mlp",
        model_class=MLPRegressor,
        default_params={
            "random_state": 42,
            "early_stopping": True,
            "n_iter_no_change": 10,
            "max_iter": 500,
        },
        search_space={
            "hidden_layer_sizes": [(64,), (128,), (64, 32), (128, 64)],
            "alpha": np.logspace(-5, -1, 10).tolist(),
            "learning_rate_init": [0.001, 0.005, 0.01],
        },
        n_iter=30,
    ),
}



# ---------------------------------------------------------------------------
# sktime Statistical Forecasting Models (Phase 96)
# ---------------------------------------------------------------------------
# Imports are lazy (inside wrapper classes) so no hard dependency at import time.
# ---------------------------------------------------------------------------
from ml.models.sktime_wrappers import (  # noqa: E402
    AutoARIMAWrapper,
    AutoETSWrapper,
    BATSWrapper,
    Catch22Wrapper,
    ExponentialSmoothingWrapper,
    MiniRocketWrapper,
    NaiveForecasterWrapper,
    RandomIntervalWrapper,
    RocketWrapper,
    ThetaForecasterWrapper,
    TimeSeriesForestWrapper,
)

SKTIME_MODELS: list[ModelConfig] = [
    ModelConfig(
        name="naive_last",
        model_class=NaiveForecasterWrapper,
        default_params={"strategy": "last"},
        search_space={"strategy": ["last", "mean", "drift"]},
        n_iter=3,
    ),
    ModelConfig(
        name="exponential_smoothing",
        model_class=ExponentialSmoothingWrapper,
        default_params={"trend": "add", "damped_trend": False},
        search_space={
            "trend": [None, "add", "mul"],
            "damped_trend": [True, False],
        },
        n_iter=6,
    ),
    ModelConfig(
        name="auto_ets",
        model_class=AutoETSWrapper,
        default_params={"auto": True, "information_criterion": "aic"},
        search_space={"information_criterion": ["aic", "bic", "aicc"]},
        n_iter=3,
    ),
    ModelConfig(
        name="theta",
        model_class=ThetaForecasterWrapper,
        default_params={"sp": 1},
        search_space={"smoothing_level": [None, 0.1, 0.2, 0.3, 0.5]},
        n_iter=5,
    ),
    ModelConfig(
        name="auto_arima",
        model_class=AutoARIMAWrapper,
        default_params={"stepwise": True, "seasonal": False, "max_p": 5, "max_q": 5},
        search_space={
            "max_p": [3, 5, 7],
            "max_q": [3, 5, 7],
            "information_criterion": ["aic", "bic"],
        },
        n_iter=6,
    ),
    ModelConfig(
        name="bats",
        model_class=BATSWrapper,
        default_params={"use_box_cox": None, "use_trend": None, "n_jobs": -1},
        search_space={
            "use_box_cox": [None, True, False],
            "use_trend": [None, True, False],
        },
        n_iter=6,
    ),
]


# ---------------------------------------------------------------------------
# sktime Regression Models (time series → scalar via 3D reshape) (Phase 96)
# ---------------------------------------------------------------------------

SKTIME_REGRESSION_MODELS: list[ModelConfig] = [
    ModelConfig(
        name="minirocket",
        model_class=MiniRocketWrapper,
        default_params={"num_kernels": 10_000, "max_dilations_per_kernel": 32},
        search_space={
            "num_kernels": [5_000, 10_000, 20_000],
        },
        n_iter=3,
    ),
    ModelConfig(
        name="rocket",
        model_class=RocketWrapper,
        default_params={"num_kernels": 10_000},
        search_space={
            "num_kernels": [5_000, 10_000, 20_000],
        },
        n_iter=3,
    ),
    ModelConfig(
        name="timeseries_forest",
        model_class=TimeSeriesForestWrapper,
        default_params={"n_estimators": 200, "min_interval": 3, "n_jobs": -1},
        search_space={
            "n_estimators": [100, 200, 500],
            "min_interval": [3, 5, 9],
        },
        n_iter=6,
    ),
    ModelConfig(
        name="random_interval",
        model_class=RandomIntervalWrapper,
        default_params={"n_estimators": 200, "n_jobs": -1},
        search_space={
            "n_estimators": [100, 200, 500],
        },
        n_iter=3,
    ),
    ModelConfig(
        name="catch22",
        model_class=Catch22Wrapper,
        default_params={"outlier_norm": False, "replace_nans": True},
        search_space={
            "outlier_norm": [True, False],
        },
        n_iter=2,
    ),
]


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

_MODEL_FAMILIES: dict[str, dict[str, ModelConfig]] = {
    "linear": LINEAR_MODELS,
    "tree": TREE_MODELS,
    "distance_neural": DISTANCE_NEURAL_MODELS,
}

if BOOSTER_MODELS:
    _MODEL_FAMILIES["booster"] = BOOSTER_MODELS


def register_model_family(family: str, configs: dict[str, ModelConfig]) -> None:
    """Register a new model family (e.g. ``"tree"``, ``"neural"``)."""
    _MODEL_FAMILIES[family] = configs


def get_model_configs(family: str = "linear") -> dict[str, ModelConfig]:
    """Return model configs for a single family."""
    if family not in _MODEL_FAMILIES:
        raise ValueError(
            f"Unknown family {family!r}. "
            f"Available: {list(_MODEL_FAMILIES.keys())}"
        )
    return _MODEL_FAMILIES[family]


def get_all_model_configs() -> dict[str, ModelConfig]:
    """Return all registered model configs across all families."""
    merged: dict[str, ModelConfig] = {}
    for configs in _MODEL_FAMILIES.values():
        merged.update(configs)
    return merged
