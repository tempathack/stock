"""Ensemble stacking — StackingRegressor with Ridge meta-learner."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline

from ml.evaluation.metrics import compute_all_metrics
from ml.models.model_configs import TrainingResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StackingEnsemble:
    """Ensemble stacking with Ridge meta-learner over top-N base models."""

    DEFAULT_TOP_N = 5
    DEFAULT_ALPHA = 1.0

    def __init__(
        self,
        top_n: int = DEFAULT_TOP_N,
        meta_learner_alpha: float = DEFAULT_ALPHA,
        cv: int = 5,
        passthrough: bool = False,
    ) -> None:
        self.top_n = top_n
        self.meta_learner_alpha = meta_learner_alpha
        self.cv = cv
        self.passthrough = passthrough
        self._stacking_model: StackingRegressor | None = None
        self._base_model_names: list[str] = []

    @property
    def base_model_names(self) -> list[str]:
        """List of base model keys selected during build()."""
        return list(self._base_model_names)

    def get_stacking_model(self) -> StackingRegressor | None:
        """Return the underlying StackingRegressor, or None if build() not called."""
        return self._stacking_model

    def build(
        self,
        results: list[TrainingResult],
        pipelines: dict[str, Pipeline],
    ) -> StackingRegressor:
        """Build the stacking ensemble from the top-N base models by OOS RMSE.

        Parameters
        ----------
        results:
            Training results for all candidate models.
        pipelines:
            Fitted pipelines keyed by ``"{model_name}_{scaler_variant}"``.

        Returns
        -------
        The constructed ``StackingRegressor`` instance.

        Raises
        ------
        ValueError
            If no valid base estimators can be assembled.
        """
        # Rank by OOS RMSE ascending (lower is better)
        sorted_results = sorted(results, key=lambda r: r.oos_metrics["rmse"])
        candidates = sorted_results[: self.top_n]

        estimators: list[tuple[str, Pipeline]] = []
        for res in candidates:
            key = f"{res.model_name}_{res.scaler_variant}"
            if key not in pipelines:
                logger.warning(
                    "Pipeline key %r missing from pipelines dict — skipping", key,
                )
                continue
            estimators.append((key, pipelines[key]))

        if not estimators:
            raise ValueError("Zero valid base estimators found for stacking ensemble.")

        meta_learner = Ridge(alpha=self.meta_learner_alpha)

        self._stacking_model = StackingRegressor(
            estimators=estimators,
            final_estimator=meta_learner,
            cv=self.cv,
            passthrough=self.passthrough,
            n_jobs=1,
        )
        self._base_model_names = [name for name, _ in estimators]

        names = ", ".join(self._base_model_names)
        logger.info(
            "Built stacking ensemble with %d base models: %s",
            len(estimators),
            names,
        )
        return self._stacking_model

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> StackingEnsemble:
        """Fit the stacking ensemble on training data.

        Raises ``RuntimeError`` if :meth:`build` has not been called.
        """
        if self._stacking_model is None:
            raise RuntimeError("build() must be called before fit().")
        self._stacking_model.fit(X_train, y_train)
        logger.info("Stacking ensemble fitted on %d samples", len(X_train))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions from the fitted ensemble.

        Raises ``RuntimeError`` if the model has not been fitted.
        """
        if self._stacking_model is None:
            raise RuntimeError("Model not fitted — call build() then fit() first.")
        return self._stacking_model.predict(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> TrainingResult:
        """Evaluate the ensemble on held-out data.

        Returns a ``TrainingResult`` compatible with the ranking and registry
        infrastructure.
        """
        y_pred = self.predict(X_test)
        metrics = compute_all_metrics(y_test, y_pred)

        logger.info(
            "Stacking ensemble OOS — RMSE=%.6f  R²=%.6f",
            metrics["rmse"],
            metrics["r2"],
        )

        return TrainingResult(
            model_name="stacking_ensemble",
            scaler_variant="meta_ridge",
            best_params={
                "top_n": self.top_n,
                "alpha": self.meta_learner_alpha,
                "n_base_models": len(self._base_model_names),
            },
            fold_metrics=[],
            oos_metrics=metrics,
            fold_stability=0.0,
        )
