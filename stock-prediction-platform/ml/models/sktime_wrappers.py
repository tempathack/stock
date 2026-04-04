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


# ===========================================================================
# sktime Regression Module Wrappers
# ===========================================================================


class SktimeRegressionWrapper(BaseEstimator, RegressorMixin):
    """Thin adapter that reshapes 2D tabular X → 3D for sktime regressors.

    sktime regressors expect X of shape (n_instances, n_dimensions, series_length).
    The existing pipeline produces X of shape (n_samples, n_features).

    This wrapper reshapes X to (n_samples, 1, n_features) — treating each sample's
    feature vector as a univariate time series of length n_features — before passing
    it to the underlying sktime regressor. The sktime model's fit/predict output is
    passed through unchanged.
    """

    def _make_regressor(self):
        """Instantiate the sktime regressor. Override in subclasses."""
        raise NotImplementedError

    def fit(self, X: np.ndarray, y: np.ndarray):
        from sklearn.base import clone

        X_3d = X.reshape(X.shape[0], 1, X.shape[1])  # (n, 1, T)
        self.regressor_ = clone(self._make_regressor())
        self.regressor_.fit(X_3d, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        check_is_fitted(self, "regressor_")
        X_3d = X.reshape(X.shape[0], 1, X.shape[1])
        return self.regressor_.predict(X_3d)


class MiniRocketWrapper(SktimeRegressionWrapper):
    """MiniROCKET — fastest ROCKET variant, state-of-the-art accuracy on CPU.

    Requires: numba (JIT compilation; results cached after first run).
    """

    def __init__(self, num_kernels: int = 10_000, max_dilations_per_kernel: int = 32):
        self.num_kernels = num_kernels
        self.max_dilations_per_kernel = max_dilations_per_kernel

    def _make_regressor(self):
        from sktime.regression.kernel_based import RocketRegressor

        return RocketRegressor(
            rocket_transform="minirocket",
            num_kernels=self.num_kernels,
            max_dilations_per_kernel=self.max_dilations_per_kernel,
        )


class RocketWrapper(SktimeRegressionWrapper):
    """ROCKET — original random convolutional kernel transform regression.

    Requires: numba.
    """

    def __init__(self, num_kernels: int = 10_000):
        self.num_kernels = num_kernels

    def _make_regressor(self):
        from sktime.regression.kernel_based import RocketRegressor

        return RocketRegressor(
            rocket_transform="rocket",
            num_kernels=self.num_kernels,
        )


class TimeSeriesForestWrapper(SktimeRegressionWrapper):
    """TimeSeriesForestRegressor — interval-based ensemble, no extra deps.

    Uses mean, std, and slope summary statistics over random time series
    intervals. Interpretable and dependency-free.
    """

    def __init__(self, n_estimators: int = 200, min_interval: int = 3,
                 n_jobs: int = -1):
        self.n_estimators = n_estimators
        self.min_interval = min_interval
        self.n_jobs = n_jobs

    def _make_regressor(self):
        from sktime.regression.interval_based import TimeSeriesForestRegressor

        return TimeSeriesForestRegressor(
            n_estimators=self.n_estimators,
            min_interval=self.min_interval,
            n_jobs=self.n_jobs,
        )


class RandomIntervalWrapper(SktimeRegressionWrapper):
    """RandomIntervalRegressor — random interval features + sklearn regressor.

    Extracts multiple summary statistics from random intervals, then applies
    a sklearn regressor (default: Ridge). No extra deps beyond core sktime.
    """

    def __init__(self, n_estimators: int = 200, n_jobs: int = -1):
        self.n_estimators = n_estimators
        self.n_jobs = n_jobs

    def _make_regressor(self):
        from sktime.regression.interval_based import RandomIntervalRegressor

        return RandomIntervalRegressor(
            n_estimators=self.n_estimators,
            n_jobs=self.n_jobs,
        )


class Catch22Wrapper(SktimeRegressionWrapper):
    """Catch22Regressor — 22 canonical time series features + sklearn regressor.

    Extracts 22 interpretable statistical features then applies a linear
    classifier. Fast inference, lightweight.
    Requires: pycatch22.
    """

    def __init__(self, outlier_norm: bool = False, replace_nans: bool = True):
        self.outlier_norm = outlier_norm
        self.replace_nans = replace_nans

    def _make_regressor(self):
        from sktime.regression.feature_based import Catch22Regressor

        return Catch22Regressor(
            outlier_norm=self.outlier_norm,
            replace_nans=self.replace_nans,
        )
