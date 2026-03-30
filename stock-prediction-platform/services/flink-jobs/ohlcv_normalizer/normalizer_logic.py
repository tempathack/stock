"""Pure Python normalization logic for the OHLCV Normalizer Flink job.

This module is intentionally kept free of any pyflink imports so that
unit tests can import and exercise it without a Flink runtime installed.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def should_include_record(
    ticker: Optional[str],
    close: Optional[Decimal],
    fetch_mode: Optional[str],
) -> bool:
    """Return True only when all inclusion criteria are met.

    Criteria (mirrors the WHERE clause in the Flink INSERT statement):
    - fetch_mode must be 'intraday'
    - ticker must not be None
    - close must not be None
    - close must be greater than 0
    """
    if fetch_mode != "intraday":
        return False
    if ticker is None:
        return False
    if close is None:
        return False
    if close <= 0:
        return False
    return True


def normalize_vwap(
    vwap: Optional[Decimal],
    close: Optional[Decimal],
) -> Optional[Decimal]:
    """Return vwap, falling back to close when vwap is None."""
    if vwap is None:
        return close
    return vwap


def round_decimal(value: Decimal, places: int = 4) -> Decimal:
    """Round a Decimal to the given number of decimal places using ROUND_HALF_UP."""
    quantize_str = Decimal("1." + "0" * places)
    return value.quantize(quantize_str, rounding=ROUND_HALF_UP)
