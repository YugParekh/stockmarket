"""Direction/confidence prediction: the original heuristic fallback plus the
backtested, calibration-validated ML model (see signal_engine/README.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.config import ML_CALIBRATION, ML_MODEL
from schemas import PredictionDirection
from signal_engine.indicators import build_features


def prediction_from_series(sentiment_scores: np.ndarray) -> tuple[PredictionDirection, int]:
    """Fallback heuristic used only when the ML model can't run (e.g. a symbol
    with insufficient daily history) — its confidence is a fabricated formula,
    not a backtested figure, which is why it's a fallback, not the primary path."""
    if len(sentiment_scores) == 0:
        return "UP", 50

    recent = sentiment_scores[-5:] if len(sentiment_scores) >= 5 else sentiment_scores
    avg_sent = float(np.mean(recent))
    slope = float(recent[-1] - recent[0]) if len(recent) > 1 else 0.0

    bullish_score = 0.6 * avg_sent + 0.4 * slope

    direction: PredictionDirection = "UP" if bullish_score >= 0 else "DOWN"
    confidence = int(min(95, max(55, (abs(bullish_score) * 80) + 55)))

    return direction, confidence


def ml_prediction(ohlcv: pd.DataFrame | None) -> tuple[PredictionDirection, int] | None:
    """
    Returns (direction, confidence) from the persisted, backtested model, where
    confidence comes from CalibrationTable.confidence_for — i.e. the ACTUAL historical
    accuracy of predictions this conviction-strength, not a formula. Returns None if the
    model artifacts aren't loaded or there isn't enough OHLCV history, so callers can
    fall back to the older heuristic.
    """
    if ML_MODEL is None or ML_CALIBRATION is None or ohlcv is None:
        return None

    features = build_features(ohlcv).dropna()
    if features.empty:
        return None

    latest = features.iloc[[-1]]
    proba_up = float(ML_MODEL.predict_proba(latest)[:, 1][0])
    direction: PredictionDirection = "UP" if proba_up >= 0.5 else "DOWN"
    confidence = ML_CALIBRATION.confidence_for(proba_up)
    return direction, confidence
