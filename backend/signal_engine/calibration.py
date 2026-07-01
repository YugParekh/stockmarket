"""
Confidence calibration: instead of a hardcoded confidence formula, this measures the
model's ACTUAL historical accuracy at different levels of prediction strength (distance
of proba_up from 0.5) on held-out walk-forward data, and uses that lookup table to
report confidence for new predictions.

An "80%-confidence" prediction from this module means: historically, predictions with
this much conviction were correct about 80% of the time on out-of-sample data. That is
the definition of "trustworthy" confidence — it is not a claim about this specific
prediction being 80% likely correct (no model can promise that), it is a track record.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CalibrationBucket:
    min_strength: float  # distance from 0.5, e.g. 0.0-0.5
    max_strength: float
    accuracy: float
    n: int


@dataclass
class CalibrationTable:
    buckets: list[CalibrationBucket]
    overall_accuracy: float
    n: int

    def confidence_for(self, proba_up: float) -> int:
        strength = abs(proba_up - 0.5)
        for b in self.buckets:
            if b.min_strength <= strength <= b.max_strength:
                return int(round(b.accuracy * 100))
        # Stronger than any observed bucket: fall back to the most extreme bucket's accuracy
        # rather than extrapolating past what backtest data supports.
        return int(round(self.buckets[-1].accuracy * 100)) if self.buckets else 50

    def to_dict(self) -> dict:
        return {
            "overall_accuracy": self.overall_accuracy,
            "n": self.n,
            "buckets": [
                {
                    "min_strength": b.min_strength,
                    "max_strength": b.max_strength,
                    "accuracy": b.accuracy,
                    "n": b.n,
                }
                for b in self.buckets
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CalibrationTable":
        return cls(
            buckets=[CalibrationBucket(**b) for b in data["buckets"]],
            overall_accuracy=data["overall_accuracy"],
            n=data["n"],
        )


def fit_calibration(proba_up: pd.Series, label: pd.Series, n_buckets: int = 8) -> CalibrationTable:
    """
    proba_up: predicted probability of UP for each out-of-sample row.
    label: actual outcome (1 = up, 0 = down) for the same rows.
    """
    strength = (proba_up - 0.5).abs()
    predicted_up = proba_up >= 0.5
    correct = (predicted_up.astype(int) == label.astype(int))

    df = pd.DataFrame({"strength": strength, "correct": correct})
    df = df.sort_values("strength").reset_index(drop=True)

    # Quantile-based bucket edges so every bucket has a comparable sample size.
    quantiles = np.linspace(0, 1, n_buckets + 1)
    edges = df["strength"].quantile(quantiles).to_numpy().copy()
    edges[0] = 0.0
    edges = np.unique(edges)

    buckets: list[CalibrationBucket] = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        is_last = i == len(edges) - 2
        mask = (df["strength"] >= lo) & (df["strength"] <= hi if is_last else df["strength"] < hi)
        subset = df.loc[mask]
        if len(subset) == 0:
            continue
        buckets.append(
            CalibrationBucket(
                min_strength=float(lo),
                max_strength=float(hi),
                accuracy=float(subset["correct"].mean()),
                n=int(len(subset)),
            )
        )

    return CalibrationTable(
        buckets=buckets,
        overall_accuracy=float(correct.mean()),
        n=int(len(df)),
    )


def calibration_report(table: CalibrationTable) -> str:
    lines = [
        f"Overall out-of-sample accuracy: {table.overall_accuracy:.1%} (n={table.n})",
        "",
        "Confidence-bucket calibration (prediction strength -> actual historical accuracy):",
        f"{'strength range':>20} | {'n':>6} | {'actual accuracy':>16}",
    ]
    for b in table.buckets:
        lines.append(
            f"{b.min_strength:.3f}-{b.max_strength:.3f}".rjust(20)
            + f" | {b.n:>6} | {b.accuracy:>15.1%}"
        )
    return "\n".join(lines)
