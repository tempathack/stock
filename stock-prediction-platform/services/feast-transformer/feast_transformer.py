"""KServe Transformer — Feast feature enrichment before predictor forwarding.

Extends kserve.Model with preprocess() that fetches features from the Feast
online store (Redis) for the requested ticker, assembles a V2 InferRequest,
and forwards it to the predictor container.

Key design decisions (from Phase 87 research):
- FeatureStore initialised ONCE at __init__ time (avoids 50-200ms registry
  fetch on every request — Feast caches registry for cache_ttl_seconds=60)
- Feature retrieval is synchronous; kserve.Model calls preprocess() from a
  thread pool for I/O-bound operations
- If all feature values are None (ticker not yet materialised), raises HTTP 400
  via kserve.errors.InvalidInput — this signals a bad/unresolvable entity to
  the client (not a transient service failure which would be 503)
- Feature column order in ONLINE_FEATURES must match training feature order
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, Union

from kserve import InferInput, InferRequest, InferResponse, Model, ModelServer, model_server

# Feature spec — order must match training sklearn pipeline column order.
# Feast to_dict() uses double-underscore as view:field separator.
ONLINE_FEATURES: list[str] = [
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:daily_return",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "lag_features_fv:lag_1",
    "lag_features_fv:rolling_mean_5",
]

# Feast to_dict() transforms "view_name:field" -> "view_name__field"
# Map from ONLINE_FEATURES to the dict keys returned by to_dict()
_FEATURE_DICT_KEYS: list[str] = [f.replace(":", "__") for f in ONLINE_FEATURES]

FEAST_STORE_PATH = os.environ.get("FEAST_STORE_PATH", "/opt/feast")


class FeastTransformer(Model):
    """KServe Model subclass that enriches inference requests with Feast features."""

    def __init__(self, name: str, feast_store_path: str = FEAST_STORE_PATH) -> None:
        super().__init__(name)
        self._feast_store_path = feast_store_path
        # Initialise FeatureStore once to avoid per-request registry metadata fetch
        from feast import FeatureStore
        self._store = FeatureStore(repo_path=self._feast_store_path)
        self.ready = True

    def _get_features(self, ticker: str) -> list[float]:
        """Fetch online features for ticker from Redis. Returns ordered float list.

        Raises:
            RuntimeError: if all feature values are None (ticker not materialised).
        """
        result: dict = self._store.get_online_features(
            features=ONLINE_FEATURES,
            entity_rows=[{"ticker": ticker.upper()}],
        ).to_dict()

        values: list[float | None] = [
            result.get(key, [None])[0] for key in _FEATURE_DICT_KEYS
        ]

        if all(v is None for v in values):
            raise RuntimeError(f"No features available in online store for ticker={ticker!r}")

        return [v if v is not None else 0.0 for v in values]

    def preprocess(
        self,
        payload: Union[Dict[str, Any], InferRequest],
        headers: Dict[str, str] | None = None,
    ) -> Union[Dict[str, Any], InferRequest]:
        """Enrich request with Feast features before forwarding to predictor.

        Expected input payload: {"ticker": "AAPL"} or V1 instances format.
        Raises HTTP 400 (InvalidInput) when features are unavailable for the
        requested ticker. HTTP 400 is correct here: the entity is unknown or
        not yet materialised — it is a client-side error (bad request entity),
        not a transient service failure (which would warrant 503).
        """
        from kserve.errors import InvalidInput

        # Extract ticker from dict or InferRequest
        if isinstance(payload, dict):
            ticker = (
                payload.get("ticker")
                or (payload.get("instances") or [{}])[0].get("ticker")
                or "UNKNOWN"
            )
        else:
            # V2 InferRequest — ticker expected in parameters
            ticker = (getattr(payload, "parameters", None) or {}).get("ticker", "UNKNOWN")

        try:
            features = self._get_features(ticker)
        except RuntimeError as exc:
            # InvalidInput maps to HTTP 400 — correct for an unresolvable entity
            raise InvalidInput(str(exc)) from exc

        infer_input = InferInput(
            name="predict",
            datatype="FP64",
            shape=[1, len(features)],
            data=features,
        )
        return InferRequest(model_name=self.name, infer_inputs=[infer_input])

    def postprocess(
        self,
        response: Union[Dict[str, Any], InferResponse],
        headers: Dict[str, str] | None = None,
    ) -> Union[Dict[str, Any], InferResponse]:
        """Pass predictor response through unchanged."""
        return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[model_server.parser])
    args, _ = parser.parse_known_args()
    model = FeastTransformer(name=args.model_name)
    ModelServer().start([model])
