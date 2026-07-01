"""
Deterministic unit tests for signal_engine/indicators.py. No network calls -
all data is synthetic, built in-test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_engine.indicators import FEATURE_COLUMNS, build_features


def _make_ohlcv(n: int = 250, seed: int = 0) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    close = 100 + np.cumsum(rng.randn(n) * 0.5)
    high = close + np.abs(rng.randn(n) * 0.3)
    low = close - np.abs(rng.randn(n) * 0.3)
    open_ = close + rng.randn(n) * 0.1
    volume = rng.randint(1000, 5000, n).astype(float)
    index = pd.bdate_range("2018-01-01", periods=n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


def test_build_features_has_all_expected_columns():
    df = _make_ohlcv()
    features = build_features(df)
    assert list(features.columns) == FEATURE_COLUMNS


def test_build_features_shape_matches_input_index():
    df = _make_ohlcv(n=300)
    features = build_features(df)
    assert len(features) == len(df)
    assert features.index.equals(df.index)


def test_rsi_bounded_zero_to_hundred():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    assert (features["rsi_14"] >= 0).all()
    assert (features["rsi_14"] <= 100).all()


def test_bollinger_percent_b_roughly_bounded():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    # %B is usually within [0, 1] but can exceed slightly during breakouts;
    # for a random-walk series it should stay within a generous sane range.
    assert features["bb_percent_b"].between(-1.5, 2.5).all()


def test_macd_hist_and_atr_and_obv_columns_present_and_finite():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    for col in ("macd_hist", "atr_pct", "obv_slope"):
        assert col in features.columns
        assert np.isfinite(features[col]).all()


def test_atr_pct_is_non_negative():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    # ATR (a range measure) divided by a positive close price should never be negative.
    assert (features["atr_pct"] >= 0).all()


def test_sma_crossover_column_present():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    assert "sma_crossover" in features.columns
    assert np.isfinite(features["sma_crossover"]).all()


def test_momentum_columns_match_manual_pct_change():
    df = _make_ohlcv(n=300)
    features = build_features(df)
    for lookback, col in ((5, "momentum_5"), (10, "momentum_10"), (20, "momentum_20")):
        expected = df["close"].pct_change(lookback)
        pd.testing.assert_series_equal(
            features[col], expected, check_names=False, rtol=1e-10
        )


def test_volume_zscore_has_reasonable_scale():
    df = _make_ohlcv(n=300)
    features = build_features(df).dropna()
    # A z-score of daily volume shouldn't realistically exceed +/-10 on this synthetic data.
    assert features["volume_zscore"].abs().max() < 10


def test_warmup_period_produces_nans_then_clears():
    df = _make_ohlcv(n=100)
    features = build_features(df)
    # The very first rows must be NaN (indicators need warm-up: e.g. SMA-50 needs 50 bars).
    assert features.iloc[0].isna().any()
    # By the end of a 100-row series all indicators should have warmed up.
    assert not features.iloc[-1].isna().any()


def test_no_lookahead_leakage_truncated_series_matches_full_prefix():
    """
    The core no-lookahead guarantee: computing indicators on a truncated series
    (missing the last k rows) must produce IDENTICAL values for the overlapping
    prefix as computing on the full series. If future rows could leak backward
    into earlier feature values, this would fail.
    """
    df = _make_ohlcv(n=300, seed=7)
    k = 30

    full = build_features(df)
    truncated = build_features(df.iloc[:-k])

    pd.testing.assert_frame_equal(
        full.iloc[: len(truncated)], truncated, check_exact=False, rtol=1e-8, atol=1e-10
    )


def test_no_lookahead_leakage_multiple_truncation_points():
    df = _make_ohlcv(n=300, seed=11)
    full = build_features(df)
    for k in (1, 5, 10, 50, 100):
        truncated = build_features(df.iloc[:-k])
        pd.testing.assert_frame_equal(
            full.iloc[: len(truncated)],
            truncated,
            check_exact=False,
            rtol=1e-8,
            atol=1e-10,
        )


def test_build_features_requires_expected_columns():
    df = _make_ohlcv(n=50).drop(columns=["volume"])
    with pytest.raises(KeyError):
        build_features(df)
