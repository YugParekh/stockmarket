"""Heuristic sentiment scoring and lexicon-based text sentiment (the original,
pre-ML heuristic layer — still used for the price/sentiment chart overlay and
as a fallback direction estimate when the ML model can't run)."""
from __future__ import annotations

from typing import Literal

import numpy as np

from schemas import SentimentBucket


def compute_point_features(
    closes: np.ndarray, volumes: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simple feature engineering for demonstration:
    - rolling return vs short moving average
    - volatility proxy
    - volume z-score
    """
    if len(closes) == 0:
        return (
            np.array([]),
            np.array([]),
            np.array([]),
        )

    window = min(10, len(closes))
    ma = np.convolve(closes, np.ones(window) / window, mode="same")
    returns = np.zeros_like(closes)
    returns[1:] = (closes[1:] - closes[:-1]) / np.where(
        closes[:-1] == 0, 1, closes[:-1]
    )

    # volatility proxy: rolling std of returns
    vol_window = min(10, len(returns))
    if vol_window > 1:
        vol = np.concatenate(
            [
                np.full(vol_window - 1, np.nan),
                np.array(
                    [
                        np.nanstd(returns[i - vol_window + 1 : i + 1])
                        for i in range(vol_window - 1, len(returns))
                    ]
                ),
            ]
        )
    else:
        vol = np.zeros_like(returns)

    vol = np.nan_to_num(vol)

    # volume z-score
    vol_mean = float(np.mean(volumes)) if len(volumes) else 0.0
    vol_std = float(np.std(volumes)) if len(volumes) else 1.0
    vol_z = (volumes - vol_mean) / (vol_std or 1.0)

    return returns, closes - ma, vol_z


def score_sentiment(
    returns: np.ndarray, price_vs_ma: np.ndarray, vol_z: np.ndarray
) -> np.ndarray:
    """
    Heuristic sentiment model:
    - positive when price is above its short MA and returns are positive
    - negative on drawdowns with elevated volatility and volumes
    Returns scores in [-1, 1].
    """
    if len(returns) == 0:
        return np.array([])

    raw = (
        1.5 * returns
        + 0.002 * price_vs_ma
        - 0.15 * np.clip(vol_z, -3, 3)
    )
    raw = np.tanh(raw * 3.0)
    return np.clip(raw, -1.0, 1.0)


def sentiment_buckets(scores: np.ndarray) -> list[SentimentBucket]:
    if len(scores) == 0:
        return [
            SentimentBucket(label="Positive", value=0),
            SentimentBucket(label="Neutral", value=0),
            SentimentBucket(label="Negative", value=0),
        ]

    pos = int(np.sum(scores > 0.1))
    neg = int(np.sum(scores < -0.1))
    neu = int(len(scores) - pos - neg)
    return [
        SentimentBucket(label="Positive", value=pos),
        SentimentBucket(label="Neutral", value=neu),
        SentimentBucket(label="Negative", value=neg),
    ]


def analyze_text_sentiment(text: str) -> float:
    """
    Very lightweight lexicon-based sentiment score in [-1, 1].
    This avoids pulling heavy ML models into the backend.
    """
    text_lower = text.lower()
    positive_words = [
        "gain",
        "gains",
        "up",
        "surge",
        "rally",
        "beat",
        "record",
        "strong",
        "bullish",
        "growth",
        "optimistic",
        "upgrade",
        "outperform",
        "profit",
    ]
    negative_words = [
        "loss",
        "down",
        "slump",
        "drop",
        "fall",
        "bearish",
        "cut",
        "downgrade",
        "miss",
        "weak",
        "selloff",
        "risk",
        "concern",
        "volatility",
    ]

    pos = sum(word in text_lower for word in positive_words)
    neg = sum(word in text_lower for word in negative_words)

    if pos == 0 and neg == 0:
        return 0.0

    score = (pos - neg) / (pos + neg)
    # squash to [-1, 1]
    return float(max(-1.0, min(1.0, score)))


def label_from_score(score: float) -> Literal["Positive", "Neutral", "Negative"]:
    if score > 0.15:
        return "Positive"
    if score < -0.15:
        return "Negative"
    return "Neutral"
