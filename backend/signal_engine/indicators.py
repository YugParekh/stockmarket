"""
Technical indicator feature engineering, built on top of the `pandas-ta` library.

KNOWN ISSUE: pandas-ta historically imports `numpy.NaN`, which was removed in
numpy>=1.24 (and does not exist in numpy 2.x). The compat shim below
(`numpy.NaN = numpy.nan`) must run BEFORE `import pandas_ta` anywhere in this
process. We verified in this environment that pandas-ta (0.4.71b0, installed
fresh into backend/.venv) imports and computes correctly once the shim is
applied first - no fallback to a hand-rolled implementation was necessary.

Every function in this module takes a DataFrame with columns:
open, high, low, close, volume (sorted ascending by date, DatetimeIndex)
and returns a Series/DataFrame aligned to the same index. Values that require
a warm-up window are NaN for the initial rows - callers must drop or handle
NaNs before using these as model features.

No lookahead: every pandas-ta indicator here is a rolling/EWM window over
strictly past-and-current bars. We never shift a feature *backward* in time;
the only intentional forward-looking shift in this whole package is the
forward-return LABEL constructed in dataset.py (never used as a feature).
"""
from __future__ import annotations

import numpy as np

# Compat shim: must run before `import pandas_ta`.
np.NaN = np.nan  # noqa: N806 - pandas-ta expects this exact attribute name

import pandas as pd
import pandas_ta as ta  # noqa: E402 - import must follow the shim above


FEATURE_COLUMNS = [
    "rsi_14",
    "macd_hist",
    "bb_percent_b",
    "atr_pct",
    "obv_slope",
    "sma_crossover",
    "ema_crossover",
    "momentum_5",
    "momentum_10",
    "momentum_20",
    "volume_zscore",
]


def _volume_zscore(volume: pd.Series, window: int = 20) -> pd.Series:
    """Rolling volume z-score - same concept as main.py's `_score_sentiment` volume
    term, reimplemented independently here (not imported from main.py)."""
    mean = volume.rolling(window, min_periods=window).mean()
    std = volume.rolling(window, min_periods=window).std(ddof=0).replace(0, np.nan)
    return (volume - mean) / std


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    df must have columns: open, high, low, close, volume, sorted ascending by date.
    Returns a DataFrame of engineered features aligned to df's index (NaNs during
    warm-up periods where the underlying rolling/EWM window isn't full yet).
    """
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]

    rsi_14 = ta.rsi(close, length=14)

    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    macd_hist_col = [c for c in macd_df.columns if c.startswith("MACDh")][0]
    macd_hist = macd_df[macd_hist_col]

    bb_df = ta.bbands(close, length=20, std=2.0)
    bb_percent_col = [c for c in bb_df.columns if c.startswith("BBP")][0]
    bb_percent_b = bb_df[bb_percent_col]

    atr_series = ta.atr(high, low, close, length=14)

    obv_series = ta.obv(close, volume)
    # OBV itself is an unbounded cumulative series; its 10-day rate of change
    # (normalized by average volume) is the stationary, model-friendly signal.
    obv_slope = obv_series.diff(10) / volume.rolling(10, min_periods=10).mean().replace(0, np.nan)

    sma_fast = ta.sma(close, length=20)
    sma_slow = ta.sma(close, length=50)
    sma_crossover = (sma_fast - sma_slow) / close

    ema_fast = ta.ema(close, length=20)
    ema_slow = ta.ema(close, length=50)
    ema_crossover = (ema_fast - ema_slow) / close

    momentum_5 = close.pct_change(5)
    momentum_10 = close.pct_change(10)
    momentum_20 = close.pct_change(20)

    vol_z = _volume_zscore(volume, window=20)

    features = pd.DataFrame(
        {
            "rsi_14": rsi_14,
            "macd_hist": macd_hist / close,
            "bb_percent_b": bb_percent_b,
            "atr_pct": atr_series / close,
            "obv_slope": obv_slope,
            "sma_crossover": sma_crossover,
            "ema_crossover": ema_crossover,
            "momentum_5": momentum_5,
            "momentum_10": momentum_10,
            "momentum_20": momentum_20,
            "volume_zscore": vol_z,
        },
        index=df.index,
    )
    return features[FEATURE_COLUMNS]
