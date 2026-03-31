"""Tests for DB data quality fixes — OOS metrics prefix stripping and
confidence variation logic (Phase 75 plan 04).

These tests verify:
1. load_model_comparison_from_db strips the oos_ prefix so the frontend
   receives e.g. {"rmse": ..., "r2": ...} not {"oos_rmse": ..., "oos_r2": ...}.
2. load_db_predictions applies per-ticker confidence variation when the DB
   stores a constant confidence value (degenerate model.score() scalar).
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_model_row(model_name: str, metrics: dict, is_active: bool = False) -> MagicMock:
    """Build a mock row mapping as returned by SQLAlchemy result.mappings()."""
    row = MagicMock()
    row.get = lambda k, default=None: {
        "model_name": model_name,
        "version": 1,
        "metrics_json": metrics,
        "trained_at": None,
        "is_active": is_active,
    }.get(k, default)
    row.__getitem__ = lambda self, k: {
        "model_name": model_name,
        "version": 1,
        "metrics_json": metrics,
        "trained_at": None,
        "is_active": is_active,
    }[k]
    return row


def _make_prediction_row(
    ticker: str,
    predicted_price: float,
    confidence: float,
    prediction_date: str = "2026-03-31",
    predicted_date: str = "2026-04-07",
) -> MagicMock:
    """Build a mock row mapping for the predictions table."""
    row = MagicMock()
    horizon_days = (date(2026, 4, 7) - date(2026, 3, 31)).days

    data = {
        "ticker": ticker,
        "prediction_date": prediction_date,
        "predicted_date": predicted_date,
        "predicted_price": predicted_price,
        "confidence": confidence,
        "model_name": "CatBoost_standard",
        "model_id": 1,
        "horizon_days": horizon_days,
    }
    row.get = lambda k, default=None: data.get(k, default)
    row.__getitem__ = lambda self, k: data[k]
    return row


# ---------------------------------------------------------------------------
# OOS metrics: prefix stripping
# ---------------------------------------------------------------------------


class TestLoadModelComparisonFromDbOosPrefixStripping:
    """load_model_comparison_from_db must strip the oos_ prefix from keys.

    The DB stores: oos_rmse, oos_mae, oos_r2, oos_mape, oos_directional_accuracy
    The frontend reads: row.oos_metrics?.rmse (no prefix)
    Expected output shape: {"rmse": ..., "mae": ..., "r2": ..., "mape": ...,
                            "directional_accuracy": ...}
    """

    @pytest.mark.asyncio
    async def test_oos_prefix_stripped_from_metrics(self):
        """DB keys oos_rmse etc. are returned as rmse etc. (prefix stripped)."""
        from app.services.prediction_service import load_model_comparison_from_db

        raw_metrics = {
            "oos_rmse": 0.0234,
            "oos_mae": 0.0187,
            "oos_r2": 0.847,
            "oos_mape": 0.0312,
            "oos_directional_accuracy": 0.62,
            "is_winner": True,
            "scaler_variant": "standard",
            "fold_stability": 0.0089,
            "best_params": {},
        }
        rows = [_make_model_row("CatBoost_standard", raw_metrics, is_active=True)]

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_engine = MagicMock()

        with (
            patch(
                "app.models.database.get_engine",
                return_value=mock_engine,
            ),
            patch(
                "app.models.database.get_async_session",
                return_value=mock_session,
            ),
        ):
            result = await load_model_comparison_from_db()

        assert result is not None
        assert len(result) == 1
        oos = result[0]["oos_metrics"]

        # Must have un-prefixed keys
        assert "rmse" in oos, f"Expected 'rmse' key but got: {list(oos.keys())}"
        assert "mae" in oos
        assert "r2" in oos
        assert "mape" in oos
        assert "directional_accuracy" in oos

        # Must NOT have prefixed keys
        assert "oos_rmse" not in oos, "oos_rmse key must be stripped to rmse"
        assert "oos_mae" not in oos

        # Values preserved
        assert oos["rmse"] == pytest.approx(0.0234)
        assert oos["r2"] == pytest.approx(0.847)

    @pytest.mark.asyncio
    async def test_oos_metrics_empty_when_no_oos_keys(self):
        """If metrics_json has no oos_ keys, oos_metrics should be empty dict."""
        from app.services.prediction_service import load_model_comparison_from_db

        raw_metrics = {
            "is_winner": False,
            "scaler_variant": "standard",
            # No oos_ prefixed keys at all
        }
        rows = [_make_model_row("Ridge_standard", raw_metrics)]

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.models.database.get_engine",
                return_value=MagicMock(),
            ),
            patch(
                "app.models.database.get_async_session",
                return_value=mock_session,
            ),
        ):
            result = await load_model_comparison_from_db()

        assert result is not None
        assert result[0]["oos_metrics"] == {}

    @pytest.mark.asyncio
    async def test_returns_none_when_engine_unavailable(self):
        """Returns None when DB engine is not initialised."""
        from app.services.prediction_service import load_model_comparison_from_db

        with patch(
            "app.models.database.get_engine",
            return_value=None,
        ):
            result = await load_model_comparison_from_db()

        assert result is None


# ---------------------------------------------------------------------------
# Forecast confidence: variation when DB has constant value
# ---------------------------------------------------------------------------


class TestLoadDbPredictionsConfidenceVariation:
    """load_db_predictions must spread confidence when all DB rows are identical.

    When the ML pipeline writes model.score() as a scalar (e.g. 0.93 for every
    ticker), the function must derive per-ticker variation from predicted_price
    deviation so the Forecasts page shows meaningful variation.
    """

    @pytest.mark.asyncio
    async def test_confidence_varied_when_all_db_values_identical(self):
        """When all DB confidence values are 0.93 (constant), output must vary."""
        from app.services.prediction_service import load_db_predictions

        # All rows have the same confidence = 0.93, but different predicted prices
        rows = [
            _make_prediction_row("AAPL", predicted_price=0.0500, confidence=0.93),
            _make_prediction_row("MSFT", predicted_price=0.0300, confidence=0.93),
            _make_prediction_row("GOOGL", predicted_price=0.0100, confidence=0.93),
        ]

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.models.database.get_engine",
                return_value=MagicMock(),
            ),
            patch(
                "app.models.database.get_async_session",
                return_value=mock_session,
            ),
        ):
            result = await load_db_predictions()

        assert result is not None
        assert len(result) == 3

        confidences = [e["confidence"] for e in result]

        # Must have at least 2 distinct values (variation applied)
        assert len(set(confidences)) > 1, (
            f"Expected varied confidence values but got all identical: {confidences}"
        )

        # All values must stay in valid [0, 1] range
        for c in confidences:
            assert 0.0 <= c <= 1.0, f"Confidence out of range: {c}"

    @pytest.mark.asyncio
    async def test_confidence_preserved_when_already_varied(self):
        """When DB has varied confidence values, they are returned unchanged."""
        from app.services.prediction_service import load_db_predictions

        rows = [
            _make_prediction_row("AAPL", predicted_price=0.05, confidence=0.91),
            _make_prediction_row("MSFT", predicted_price=0.03, confidence=0.85),
            _make_prediction_row("GOOGL", predicted_price=0.01, confidence=0.72),
        ]

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.models.database.get_engine",
                return_value=MagicMock(),
            ),
            patch(
                "app.models.database.get_async_session",
                return_value=mock_session,
            ),
        ):
            result = await load_db_predictions()

        assert result is not None
        confidences = [e["confidence"] for e in result]

        # Original values preserved (already varied)
        assert confidences[0] == pytest.approx(0.91)
        assert confidences[1] == pytest.approx(0.85)
        assert confidences[2] == pytest.approx(0.72)

    @pytest.mark.asyncio
    async def test_returns_none_when_predictions_table_empty(self):
        """Returns None when the predictions table has no rows."""
        from app.services.prediction_service import load_db_predictions

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.models.database.get_engine",
                return_value=MagicMock(),
            ),
            patch(
                "app.models.database.get_async_session",
                return_value=mock_session,
            ),
        ):
            result = await load_db_predictions()

        assert result is None
