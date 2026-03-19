"""Sklearn transformer pipelines — StandardScaler, QuantileTransformer, MinMaxScaler."""

from __future__ import annotations

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer, StandardScaler

# Available scaler variants
SCALER_VARIANTS: tuple[str, ...] = ("standard", "quantile", "minmax")

_SCALER_MAP = {
    "standard": lambda: StandardScaler(),
    "quantile": lambda: QuantileTransformer(
        output_distribution="normal", random_state=42
    ),
    "minmax": lambda: MinMaxScaler(),
}


def build_scaler_pipeline(variant: str) -> Pipeline:
    """Return an sklearn Pipeline containing a single scaler step.

    Parameters
    ----------
    variant:
        One of ``"standard"``, ``"quantile"``, or ``"minmax"``.

    Returns
    -------
    Pipeline with a ``("scaler", <ScalerInstance>)`` step.  The model step
    is added later during training (Phase 12+).

    Raises
    ------
    ValueError
        If *variant* is not one of :data:`SCALER_VARIANTS`.
    """
    if variant not in _SCALER_MAP:
        raise ValueError(
            f"Unknown scaler variant {variant!r}. "
            f"Choose from {SCALER_VARIANTS}."
        )
    return Pipeline([("scaler", _SCALER_MAP[variant]())])
