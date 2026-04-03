"""Unit tests for FeastTransformer — KServe preprocess() hook with Feast online features.

Covers:
  PIT-02 — preprocess() calls get_online_features() and returns a V2 InferRequest
  PIT-03 — preprocess() raises kserve.errors.InvalidInput (HTTP 400) when all features are None

Run: cd stock-prediction-platform/services/api && pytest tests/test_feast_transformer.py -x -q
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Make feast_transformer importable from its service directory.
# Path from tests/ (services/api/tests/): ../../feast-transformer
_TRANSFORMER_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../feast-transformer")
)
if _TRANSFORMER_DIR not in sys.path:
    sys.path.insert(0, _TRANSFORMER_DIR)


@pytest.fixture()
def mock_feature_store():
    """Return a MagicMock FeatureStore that yields realistic feature values."""
    store = MagicMock()
    result = MagicMock()
    # Simulate Feast to_dict() output (double-underscore separator)
    result.to_dict.return_value = {
        "ohlcv_stats_fv__close":         [185.0],
        "ohlcv_stats_fv__daily_return":  [0.012],
        "technical_indicators_fv__rsi_14":   [58.3],
        "technical_indicators_fv__macd_line": [1.4],
        "lag_features_fv__lag_1":        [183.2],
        "lag_features_fv__rolling_mean_5": [181.5],
    }
    store.get_online_features.return_value = result
    return store


@pytest.fixture()
def mock_null_feature_store():
    """Return a MagicMock FeatureStore where all features are None (ticker not materialised)."""
    store = MagicMock()
    result = MagicMock()
    result.to_dict.return_value = {
        "ohlcv_stats_fv__close":         [None],
        "ohlcv_stats_fv__daily_return":  [None],
        "technical_indicators_fv__rsi_14":   [None],
        "technical_indicators_fv__macd_line": [None],
        "lag_features_fv__lag_1":        [None],
        "lag_features_fv__rolling_mean_5": [None],
    }
    store.get_online_features.return_value = result
    return store


def _make_transformer(mock_store):
    """Helper: build FeastTransformer with a pre-built mock FeatureStore."""
    with patch("feast.FeatureStore", return_value=mock_store):
        import feast_transformer as ft_module
        transformer = ft_module.FeastTransformer.__new__(ft_module.FeastTransformer)
        # Manually init to inject mock store
        transformer.name = "stock-model-serving"
        transformer._feast_store_path = "/fake/feast"
        transformer._store = mock_store
        transformer.ready = True
        return transformer


def test_preprocess_builds_v2_request(mock_feature_store):
    """preprocess() returns InferRequest with shape [1, 6] and 6 float values."""
    import feast_transformer as ft_module
    transformer = _make_transformer(mock_feature_store)

    payload = {"ticker": "AAPL"}
    result = transformer.preprocess(payload)

    # Must be an InferRequest
    from kserve import InferRequest
    assert isinstance(result, InferRequest)

    inputs = result.inputs
    assert len(inputs) == 1
    inp = inputs[0]
    assert inp.name == "predict"
    assert inp.datatype == "FP64"
    assert inp.shape == [1, 6]
    assert len(inp.data) == 6
    assert all(isinstance(v, float) for v in inp.data)
    # Verify Feast was called with the ticker
    mock_feature_store.get_online_features.assert_called_once()
    call_kwargs = mock_feature_store.get_online_features.call_args[1]
    assert call_kwargs["entity_rows"] == [{"ticker": "AAPL"}]


def test_preprocess_no_features_raises(mock_null_feature_store):
    """preprocess() raises kserve.errors.InvalidInput (HTTP 400) when all features are None."""
    import feast_transformer as ft_module
    from kserve.errors import InvalidInput
    transformer = _make_transformer(mock_null_feature_store)

    payload = {"ticker": "ZZZZ"}
    with pytest.raises(InvalidInput):
        transformer.preprocess(payload)


def test_get_features_maps_none_to_zero(mock_feature_store):
    """_get_features() substitutes 0.0 for None values when at least one is non-None."""
    import feast_transformer as ft_module

    # Partial None result: two features are None
    partial_result = MagicMock()
    partial_result.to_dict.return_value = {
        "ohlcv_stats_fv__close":         [185.0],
        "ohlcv_stats_fv__daily_return":  [None],   # None -> 0.0
        "technical_indicators_fv__rsi_14":   [58.3],
        "technical_indicators_fv__macd_line": [None],  # None -> 0.0
        "lag_features_fv__lag_1":        [183.2],
        "lag_features_fv__rolling_mean_5": [181.5],
    }
    mock_feature_store.get_online_features.return_value = partial_result
    transformer = _make_transformer(mock_feature_store)

    features = transformer._get_features("MSFT")
    assert len(features) == 6
    assert features[1] == 0.0   # daily_return was None
    assert features[3] == 0.0   # macd_line was None
    assert features[0] == 185.0


def test_feast_store_initialised_once():
    """FeatureStore.__init__ is called exactly once, at FeastTransformer init time."""
    import feast_transformer as ft_module

    mock_store_instance = MagicMock()
    with patch("feast.FeatureStore", return_value=mock_store_instance) as mock_fs_cls:
        transformer = ft_module.FeastTransformer(name="test-model", feast_store_path="/fake")

    assert mock_fs_cls.call_count == 1
    # Subsequent preprocess calls must NOT create new FeatureStore instances
    result_mock = MagicMock()
    result_mock.to_dict.return_value = {
        k: [1.0] for k in [
            "ohlcv_stats_fv__close", "ohlcv_stats_fv__daily_return",
            "technical_indicators_fv__rsi_14", "technical_indicators_fv__macd_line",
            "lag_features_fv__lag_1", "lag_features_fv__rolling_mean_5",
        ]
    }
    mock_store_instance.get_online_features.return_value = result_mock
    transformer.preprocess({"ticker": "AAPL"})
    transformer.preprocess({"ticker": "MSFT"})

    # Still only one FeatureStore init
    assert mock_fs_cls.call_count == 1
