"""sklearn-compatible wrappers for sktime statistical forecasters.

Each wrapper implements ``fit(X, y) -> self`` and ``predict(X) -> ndarray``
so they plug into the existing ``Pipeline([scaler, model])`` infrastructure
in ``model_trainer.py`` without any core changes.

Design contract
---------------
- ``fit(X, y)``:  fits the internal sktime/statsmodels forecaster on ``y``
  treated as a univariate time series (X is ignored; lag structure in X is
  handled by the sklearn scaler step upstream).
- ``predict(X)``:  returns the 1-step-ahead out-of-sample forecast from the
  last fitted state, broadcast to len(X) rows so RandomizedSearchCV scoring
  works correctly.

This approach is intentionally simple — the statistical forecasters contribute
autocorrelation-based signal while the existing feature-engineered models
handle cross-sectional and macro signals. Both families are evaluated on the
same OOS RMSE metric for fair comparison.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_is_fitted


class _SktimeBase(BaseEstimator, RegressorMixin):
    """Abstract base for all sktime wrappers."""

    def _to_series(self, y: np.ndarray) -> pd.Series:
        """Convert numpy array to a pd.Series with a PeriodIndex (daily)."""
        idx = pd.period_range(start="2000-01-01", periods=len(y), freq="B")
        return pd.Series(y, index=idx, dtype=float)

    def predict(self, X: np.ndarray) -> np.ndarray:
        check_is_fitted(self, "forecast_value_")
        return np.full(len(X), self.forecast_value_, dtype=float)


class NaiveForecasterWrapper(_SktimeBase):
    """NaiveForecaster(strategy='last') — strongest naive baseline."""

    def __init__(self, strategy: str = "last"):
        self.strategy = strategy

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sktime.forecasting.naive import NaiveForecaster

        series = self._to_series(y)
        fc = NaiveForecaster(strategy=self.strategy, sp=1)
        fc.fit(series, fh=[1])
        self.forecast_value_ = float(fc.predict().iloc[0])
        return self


class ExponentialSmoothingWrapper(_SktimeBase):
    """Holt-Winters ExponentialSmoothing via statsmodels."""

    def __init__(self, trend: str | None = "add", damped_trend: bool = False,
                 seasonal: str | None = None):
        self.trend = trend
        self.damped_trend = damped_trend
        self.seasonal = seasonal

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sktime.forecasting.exp_smoothing import ExponentialSmoothing

        series = self._to_series(y)
        fc = ExponentialSmoothing(
            trend=self.trend,
            damped_trend=self.damped_trend,
            seasonal=self.seasonal,
        )
        fc.fit(series, fh=[1])
        self.forecast_value_ = float(fc.predict().iloc[0])
        return self


class AutoETSWrapper(_SktimeBase):
    """AutoETS — automatically selects error/trend/seasonal components."""

    def __init__(self, auto: bool = True, information_criterion: str = "aic"):
        self.auto = auto
        self.information_criterion = information_criterion

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sktime.forecasting.ets import AutoETS

        series = self._to_series(y)
        fc = AutoETS(auto=self.auto, information_criterion=self.information_criterion,
                     sp=1, n_jobs=-1)
        fc.fit(series, fh=[1])
        self.forecast_value_ = float(fc.predict().iloc[0])
        return self


class ThetaForecasterWrapper(_SktimeBase):
    """ThetaForecaster — M3 competition winner, fast and reliable."""

    def __init__(self, smoothing_level: float | None = None, sp: int = 1):
        self.smoothing_level = smoothing_level
        self.sp = sp

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sktime.forecasting.theta import ThetaForecaster

        series = self._to_series(y)
        fc = ThetaForecaster(smoothing_level=self.smoothing_level, sp=self.sp)
        fc.fit(series, fh=[1])
        self.forecast_value_ = float(fc.predict().iloc[0])
        return self


class AutoARIMAWrapper(_SktimeBase):
    """AutoARIMA via pmdarima — automatically selects p, d, q orders.

    Uses pmdarima (not sktime's wrapper) for speed; pmdarima is ~10x faster
    than statsmodels ARIMA with stepwise search enabled.
    """

    def __init__(self, stepwise: bool = True, seasonal: bool = False,
                 max_p: int = 5, max_q: int = 5, information_criterion: str = "aic"):
        self.stepwise = stepwise
        self.seasonal = seasonal
        self.max_p = max_p
        self.max_q = max_q
        self.information_criterion = information_criterion

    def fit(self, X: np.ndarray, y: np.ndarray):
        import pmdarima as pm

        model = pm.auto_arima(
            y,
            stepwise=self.stepwise,
            seasonal=self.seasonal,
            max_p=self.max_p,
            max_q=self.max_q,
            information_criterion=self.information_criterion,
            error_action="ignore",
            suppress_warnings=True,
        )
        self.model_ = model
        self.forecast_value_ = float(model.predict(n_periods=1)[0])
        return self


class BATSWrapper(_SktimeBase):
    """BATS — handles multiple seasonalities via Box-Cox + ARMA + Trigonometric."""

    def __init__(self, use_box_cox: bool | None = None,
                 use_trend: bool | None = None, n_jobs: int = -1):
        self.use_box_cox = use_box_cox
        self.use_trend = use_trend
        self.n_jobs = n_jobs

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sktime.forecasting.bats import BATS

        series = self._to_series(y)
        fc = BATS(
            use_box_cox=self.use_box_cox,
            use_trend=self.use_trend,
            n_jobs=self.n_jobs,
        )
        fc.fit(series, fh=[1])
        self.forecast_value_ = float(fc.predict().iloc[0])
        return self
