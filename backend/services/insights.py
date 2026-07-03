"""Builds the Insights payload (nextMove, risk, commentary) from a price series
and the already-computed direction/confidence."""
from __future__ import annotations

from typing import Literal

import numpy as np

from schemas import Insights, PredictionDirection, PredictionSummary, RiskSummary


def build_insights(
    symbol: str,
    closes: np.ndarray,
    sentiment_scores: np.ndarray,
    direction: PredictionDirection,
    confidence: int,
    is_ml_backed: bool = False,
) -> Insights:
    if len(closes) == 0:
        return Insights(
            nextMove=PredictionSummary(
                direction="UP",
                confidence=50,
                expectedReturnPct=0.0,
                volatilityScore=0.0,
                horizon="next 1–3 sessions",
            ),
            risk=RiskSummary(level="Medium", valueAtRiskPct=2.0),
            commentary=f"Not enough recent data for {symbol} to compute a directional view.",
        )

    # Approximate daily returns from closes
    returns = np.zeros_like(closes, dtype=float)
    returns[1:] = (closes[1:] - closes[:-1]) / np.where(closes[:-1] == 0, 1, closes[:-1])
    recent = returns[-10:] if len(returns) > 10 else returns
    avg_ret = float(np.mean(recent)) if len(recent) else 0.0
    vol = float(np.std(recent)) if len(recent) else 0.0

    expected_return_pct = float(round(avg_ret * 100.0, 2))
    volatility_score = float(round(min(100.0, vol * 1000.0), 1))

    # Simple risk level based on volatility
    if volatility_score < 25:
        risk_level: Literal["Low", "Medium", "High"] = "Low"
    elif volatility_score < 55:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # 95% one-day VaR approximation
    value_at_risk_pct = float(round(1.65 * vol * 100.0, 2))

    # Sentiment overlay for commentary
    recent_sent = (
        sentiment_scores[-10:] if len(sentiment_scores) >= 10 else sentiment_scores
    )
    avg_sent = float(np.mean(recent_sent)) if len(recent_sent) else 0.0

    if avg_sent > 0.25:
        sent_label = "strongly bullish"
    elif avg_sent > 0.05:
        sent_label = "slightly bullish"
    elif avg_sent < -0.25:
        sent_label = "strongly bearish"
    elif avg_sent < -0.05:
        sent_label = "slightly bearish"
    else:
        sent_label = "broadly neutral"

    dir_word = "upside" if direction == "UP" else "downside"
    if is_ml_backed:
        # confidence here is a backtested historical-accuracy figure (see
        # signal_engine/README.md), not a claim about this specific prediction — it is
        # deliberately capped low (typically 45-58%) because that is what the real
        # backtest supports. A naive "assume the market goes up" baseline scores ~54-57%
        # over the same historical window, so this is explicitly framed as a weak signal.
        commentary = (
            f"Backtested model leans {dir_word} on {symbol}: {confidence}% historical "
            f"accuracy for predictions this strong (not a strong edge — a naive "
            f"'assume uptrend' baseline scores similarly over the same backtest window), "
            f"{sent_label} news tone, and an estimated ±{value_at_risk_pct:.2f}% one-day risk band."
        )
    else:
        commentary = (
            f"Insufficient daily history for a calibrated model prediction on {symbol}; "
            f"falling back to an unvalidated heuristic that leans {dir_word} with "
            f"{sent_label} news tone and an estimated ±{value_at_risk_pct:.2f}% one-day "
            f"risk band. Treat this heuristic fallback with more skepticism than a "
            f"calibrated prediction."
        )

    return Insights(
        nextMove=PredictionSummary(
            direction=direction,
            confidence=confidence,
            expectedReturnPct=expected_return_pct,
            volatilityScore=volatility_score,
            horizon="next 1–3 sessions",
        ),
        risk=RiskSummary(level=risk_level, valueAtRiskPct=value_at_risk_pct),
        commentary=commentary,
    )
