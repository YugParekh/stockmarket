"""
Engine registry: picks which signal-generation approach is "current" for
production use, based on what backtest.py's real walk-forward results
actually showed - not an upfront assumption.

IMPORTANT: this module does NOT wire into backend/main.py. That integration
is an intentionally separate, future task. This module only exposes a stable
interface (`get_current_engine`) that a future caller can use, plus the
calibration table needed to convert a raw model score into an honest,
backtest-derived confidence number.

--- Verdict, derived from the real run recorded in signal_engine/README.md ---

Real walk-forward backtest, 8 symbols (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA,
SPY, QQQ), ~8 years of daily bars each (2018-07 to 2026-06), n=13,048
out-of-sample predictions per horizon:

  Horizon | Rule-based | ML     | Baseline: always-up | Baseline: prev-day
  1-day   | 51.24%     | 52.68% | 53.66%               | 49.63%
  5-day   | 53.85%     | 53.89% | 56.62%               | 50.08%

KEY FINDING: the naive "always predict UP" baseline BEATS both engines on
BOTH horizons. This is because the 8 chosen symbols are large, currently-
successful companies/ETFs in a period that was net bullish - "always up" is
a strong baseline precisely because of that survivorship/selection bias, not
because it is a genuinely skillful predictor. Neither engine demonstrates a
real, practically useful edge over naive baselines here. The ML classifier
is marginally better than the rule-based ensemble on both horizons, but
"marginally better than another engine that already loses to a naive
baseline" is not a basis for shipping either one as a trading signal.

Calibration is also NOT cleanly monotonic in the real run: e.g. for the
rule-based engine at the 1-day horizon, the single highest-conviction bucket
(strength 0.245-0.479) had the WORST accuracy of all eight buckets (48.9%,
i.e. worse than a coin flip) - see README.md's calibration tables. This is
reported plainly, not smoothed over: it means a naive "higher raw score ->
higher confidence" assumption does NOT hold reliably in this data, which is
exactly the failure mode real calibration is meant to catch and expose.

Given all of this, the registry's default posture is conservative: it
exposes both engines and their genuine calibration tables so a caller can
make an informed choice, but SHIP_TO_PRODUCTION is False for every horizon.
Neither engine should be presented to real traders as an actionable signal
based on this backtest. `RECOMMENDED_ENGINE` records the engine with the
(very small) edge in the real backtest per horizon, purely for reference -
it is not an endorsement of production-readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import pandas as pd

from signal_engine import rule_based
from signal_engine.calibration import CalibrationTable

EngineName = Literal["rule_based", "ml"]

# Filled in from the real backtest.py run (see README.md "Results" tables).
# Kept as an explicit, hand-set constant (not auto-derived at import time) so
# that using this registry never requires a live backtest run or network
# access - it is a frozen record of what the offline backtest found.
#
# Populated after running backend/signal_engine/backtest.py end-to-end on
# real yfinance data for AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, SPY, QQQ.
RECOMMENDED_ENGINE: dict[int, EngineName] = {
    1: "ml",
    5: "ml",
}

# Whether the recommended engine's edge over the better naive baseline was
# large enough, in the real backtest, to be worth surfacing to end users as
# an actionable trading signal (as opposed to merely "a slightly-less-naive
# coin flip"). See README.md "Verdict" section for the reasoning.
SHIP_TO_PRODUCTION: dict[int, bool] = {
    1: False,
    5: False,
}


@dataclass
class CurrentEngine:
    name: EngineName
    horizon: int
    predict_proba_up: Callable[[pd.DataFrame], pd.Series]
    calibration: CalibrationTable | None
    ship_to_production: bool

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Returns a DataFrame indexed like `features` with columns:
        proba_up, direction ("UP"/"DOWN"), confidence (0-100, calibration-derived
        if a calibration table is attached, else a neutral 50)."""
        proba_up = self.predict_proba_up(features)
        direction = proba_up.apply(lambda p: "UP" if p >= 0.5 else "DOWN")
        if self.calibration is not None:
            confidence = proba_up.apply(self.calibration.confidence_for)
        else:
            confidence = pd.Series(50, index=features.index)
        return pd.DataFrame(
            {"proba_up": proba_up, "direction": direction, "confidence": confidence},
            index=features.index,
        )


def get_current_engine(
    horizon: int = 1, calibration: CalibrationTable | None = None
) -> CurrentEngine:
    """
    Returns the engine recommended by the real backtest for the given horizon
    (1 or 5 trading days).

    `calibration` should be the CalibrationTable produced by
    backtest.run_backtest_for_horizon(...).<engine>.calibration for the SAME
    horizon/engine - callers are expected to load this from a persisted
    backtest run (see backtest.save_reports) rather than recomputing it live,
    since calibration is only meaningful when derived from genuine historical
    out-of-sample predictions.
    """
    if horizon not in RECOMMENDED_ENGINE:
        raise ValueError(f"No recommendation recorded for horizon={horizon}")

    name = RECOMMENDED_ENGINE[horizon]
    ship = SHIP_TO_PRODUCTION[horizon]

    if name == "rule_based":
        predict_fn = rule_based.predict_proba_up
    elif name == "ml":
        raise NotImplementedError(
            "The ML engine requires a fitted model artifact from the walk-forward "
            "run; wiring a persisted model into this registry is left to the "
            "future main.py-integration task, not part of this module's scope."
        )
    else:  # pragma: no cover - exhaustiveness guard
        raise ValueError(f"Unknown engine name: {name}")

    return CurrentEngine(
        name=name,
        horizon=horizon,
        predict_proba_up=predict_fn,
        calibration=calibration,
        ship_to_production=ship,
    )
