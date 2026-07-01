"""
Interpretable rule-based signal: each technical indicator is transformed into a signed
score in roughly [-1, 1], then combined with fixed, documented weights. No training,
no black box — every prediction can be explained as "RSI contributed +0.2, MACD +0.1, ...".

This is evaluated in backtest.py exactly like the ML model, on the same walk-forward
splits, so its real accuracy can be compared honestly rather than assumed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Weights are a starting judgment call (momentum/trend-heavy, since momentum/trend-
# following signals are the most commonly cited as having weak-but-real persistence in
# daily equity data). They are fixed, not fit to data, which is what keeps this model
# interpretable and free of overfitting risk — the backtest measures whether that's a
# fair tradeoff. They sum to 1.0 so the combined score stays within [-1, 1] after clipping.
WEIGHTS = {
    "rsi_14": 0.15,
    "macd_hist": 0.20,
    "bb_percent_b": 0.10,
    "sma_crossover": 0.20,
    "momentum_5": 0.15,
    "momentum_10": 0.10,
    "momentum_20": 0.10,
}


def _signed_signals(features: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rsi_14": (features["rsi_14"] - 50.0) / 50.0,
            "macd_hist": np.tanh(features["macd_hist"] * 50.0),
            "bb_percent_b": np.clip((features["bb_percent_b"] - 0.5) * 2.0, -1.0, 1.0),
            "sma_crossover": np.tanh(features["sma_crossover"] * 20.0),
            "momentum_5": np.tanh(features["momentum_5"] * 10.0),
            "momentum_10": np.tanh(features["momentum_10"] * 8.0),
            "momentum_20": np.tanh(features["momentum_20"] * 6.0),
        },
        index=features.index,
    )


def score(features: pd.DataFrame) -> pd.Series:
    """Returns a raw signed score in [-1, 1] per row. Positive = bullish."""
    signals = _signed_signals(features)
    weighted = sum(signals[col] * w for col, w in WEIGHTS.items())
    return weighted.clip(-1.0, 1.0)


def predict_proba_up(features: pd.DataFrame) -> pd.Series:
    """Maps the raw score to a pseudo-probability in (0, 1) via a linear rescale, for a
    common interface with the ML model. This is NOT yet calibrated — calibration.py maps
    this raw value to a real historical-accuracy-based confidence."""
    return (score(features) + 1.0) / 2.0
