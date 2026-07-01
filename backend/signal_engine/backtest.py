"""
Full walk-forward backtest across a symbol list, for both engines (rule-based,
ML) and both horizons (1-day, 5-day forward direction), compared against two
naive baselines on the exact same out-of-sample rows.

Walk-forward protocol (expanding window, no lookahead):
  - Data is pooled across symbols and sorted by date.
  - The dataset's first MIN_TRAIN_YEARS calendar years are reserved purely for
    training (never scored).
  - For each subsequent calendar year Y, both engines are "trained" (the ML
    model literally refits; the rule-based engine's fixed weights don't
    change, but it is scored on the same expanding-window split for a fair
    comparison) using only rows with date < start of Y, and then produce
    predictions for every row within year Y. This mirrors periodic annual
    retraining in production: never train on the future relative to what is
    being predicted.
  - Predictions for every year from MIN_TRAIN_YEARS onward are concatenated
    into one out-of-sample (OOS) prediction stream per symbol/horizon/engine.
    This OOS stream is what all accuracy numbers and calibration.py's bucket
    table are computed from - never in-sample predictions.

Naive baselines, computed on the identical OOS rows so the comparison is
apples-to-apples:
  - always_up: predict "UP" every time.
  - previous_day: predict the same direction as the prior trading day's
    1-day move (persistence baseline).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from signal_engine import rule_based
from signal_engine.calibration import CalibrationTable, fit_calibration
from signal_engine.dataset import DEFAULT_SYMBOLS, SymbolDataset, build_all_datasets
from signal_engine.indicators import FEATURE_COLUMNS
from signal_engine.ml_model import MIN_TRAIN_YEARS, walk_forward_predict

RESULTS_DIR = Path(__file__).parent / "data_cache" / "backtest_results"


@dataclass
class EngineResult:
    engine: str
    horizon: int
    oos: pd.DataFrame  # columns: symbol, date, proba_up, label
    calibration: CalibrationTable

    @property
    def overall_accuracy(self) -> float:
        pred_up = (self.oos["proba_up"] >= 0.5).astype(int)
        return float((pred_up == self.oos["label"]).mean())

    def per_symbol_accuracy(self) -> dict[str, float]:
        out = {}
        for symbol, grp in self.oos.groupby("symbol"):
            pred_up = (grp["proba_up"] >= 0.5).astype(int)
            out[symbol] = float((pred_up == grp["label"]).mean())
        return out


@dataclass
class BaselineResult:
    name: str
    horizon: int
    oos: pd.DataFrame  # columns: symbol, date, pred, label

    @property
    def overall_accuracy(self) -> float:
        return float((self.oos["pred"] == self.oos["label"]).mean())

    def per_symbol_accuracy(self) -> dict[str, float]:
        out = {}
        for symbol, grp in self.oos.groupby("symbol"):
            out[symbol] = float((grp["pred"] == grp["label"]).mean())
        return out


@dataclass
class BacktestReport:
    horizon: int
    rule_based: EngineResult
    ml: EngineResult
    baseline_always_up: BaselineResult
    baseline_previous_day: BaselineResult
    symbols_used: list[str]
    symbols_failed: list[str] = field(default_factory=list)


def _rule_based_walk_forward(
    datasets: dict[str, SymbolDataset], label_col: str
) -> pd.DataFrame:
    """
    Scores the rule-based engine on the SAME expanding-window OOS rows the ML
    model uses (first MIN_TRAIN_YEARS years excluded), even though its fixed
    weights don't change across folds - this keeps the comparison apples to
    apples (identical row set, identical "hasn't seen this year yet" cutoff).
    """
    frames = []
    for symbol, ds in datasets.items():
        f = ds.frame[FEATURE_COLUMNS + [label_col]].copy()
        f.index = f.index.rename(None)
        f["symbol"] = symbol
        f["date"] = f.index
        frames.append(f)
    pooled = pd.concat(frames, axis=0).sort_values("date").reset_index(drop=True)
    pooled["year"] = pooled["date"].dt.year

    years = sorted(pooled["year"].unique())
    if len(years) <= MIN_TRAIN_YEARS:
        raise ValueError("Not enough distinct years of history for walk-forward validation")

    cutoff_years = years[MIN_TRAIN_YEARS:]
    oos_mask = pooled["year"].isin(cutoff_years)
    oos = pooled.loc[oos_mask].copy()

    proba_up = rule_based.predict_proba_up(oos[FEATURE_COLUMNS])
    return pd.DataFrame(
        {
            "symbol": oos["symbol"].values,
            "date": oos["date"].values,
            "proba_up": proba_up.values,
            "label": oos[label_col].values,
        }
    ).sort_values("date").reset_index(drop=True)


def _baseline_always_up(oos_rows: pd.DataFrame) -> pd.DataFrame:
    out = oos_rows[["symbol", "date", "label"]].copy()
    out["pred"] = 1
    return out


def _baseline_previous_day(
    datasets: dict[str, SymbolDataset], label_col: str, oos_rows: pd.DataFrame
) -> pd.DataFrame:
    """Predicts the same direction as the previous trading day's 1-day realized
    move (a classic persistence/momentum-naive baseline), evaluated on the same
    OOS (symbol, date) rows as the model engines."""
    records = []
    for symbol, ds in datasets.items():
        frame = ds.frame
        prev_move_up = (frame["close"].diff() > 0).astype(int)
        sub = pd.DataFrame({"date": frame.index, "pred": prev_move_up.values})
        sub["symbol"] = symbol
        records.append(sub)
    prev_moves = pd.concat(records, axis=0)

    merged = oos_rows[["symbol", "date", "label"]].merge(
        prev_moves, on=["symbol", "date"], how="left"
    )
    merged["pred"] = merged["pred"].fillna(1).astype(int)  # no prior day -> default UP
    return merged


def run_backtest_for_horizon(
    datasets: dict[str, SymbolDataset], horizon: int
) -> BacktestReport:
    label_col = f"label_{horizon}"

    ml_oos = walk_forward_predict(datasets, label_col)
    rb_oos = _rule_based_walk_forward(datasets, label_col)

    ml_calibration = fit_calibration(ml_oos["proba_up"], ml_oos["label"])
    rb_calibration = fit_calibration(rb_oos["proba_up"], rb_oos["label"])

    baseline_up = BaselineResult(
        name="always_up", horizon=horizon, oos=_baseline_always_up(ml_oos)
    )
    baseline_prev = BaselineResult(
        name="previous_day",
        horizon=horizon,
        oos=_baseline_previous_day(datasets, label_col, ml_oos),
    )

    return BacktestReport(
        horizon=horizon,
        rule_based=EngineResult(
            engine="rule_based", horizon=horizon, oos=rb_oos, calibration=rb_calibration
        ),
        ml=EngineResult(engine="ml", horizon=horizon, oos=ml_oos, calibration=ml_calibration),
        baseline_always_up=baseline_up,
        baseline_previous_day=baseline_prev,
        symbols_used=sorted(datasets.keys()),
    )


def run_full_backtest(
    symbols: list[str] | None = None, period: str = "8y"
) -> dict[int, BacktestReport]:
    symbols = symbols or DEFAULT_SYMBOLS
    datasets = build_all_datasets(symbols, period=period)
    failed = [s for s in symbols if s not in datasets]

    reports: dict[int, BacktestReport] = {}
    for horizon in (1, 5):
        report = run_backtest_for_horizon(datasets, horizon)
        report.symbols_failed = failed
        reports[horizon] = report
    return reports


def _engine_summary(result: EngineResult) -> dict:
    return {
        "engine": result.engine,
        "horizon": result.horizon,
        "overall_accuracy": result.overall_accuracy,
        "n": int(len(result.oos)),
        "per_symbol_accuracy": result.per_symbol_accuracy(),
        "calibration_buckets": [
            {
                "min_strength": b.min_strength,
                "max_strength": b.max_strength,
                "accuracy": b.accuracy,
                "n": b.n,
            }
            for b in result.calibration.buckets
        ],
    }


def _baseline_summary(result: BaselineResult) -> dict:
    return {
        "name": result.name,
        "horizon": result.horizon,
        "overall_accuracy": result.overall_accuracy,
        "n": int(len(result.oos)),
        "per_symbol_accuracy": result.per_symbol_accuracy(),
    }


def report_to_dict(report: BacktestReport) -> dict:
    return {
        "horizon": report.horizon,
        "symbols_used": report.symbols_used,
        "symbols_failed": report.symbols_failed,
        "rule_based": _engine_summary(report.rule_based),
        "ml": _engine_summary(report.ml),
        "baseline_always_up": _baseline_summary(report.baseline_always_up),
        "baseline_previous_day": _baseline_summary(report.baseline_previous_day),
    }


def save_reports(reports: dict[int, BacktestReport], path: Path | None = None) -> Path:
    path = path or (RESULTS_DIR / "latest_backtest.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {str(h): report_to_dict(r) for h, r in reports.items()}
    path.write_text(json.dumps(payload, indent=2, default=float))
    return path


if __name__ == "__main__":
    reports = run_full_backtest()
    out_path = save_reports(reports)
    for horizon, report in reports.items():
        print(f"\n=== Horizon: {horizon}-day ===")
        print(f"Rule-based accuracy: {report.rule_based.overall_accuracy:.1%} (n={len(report.rule_based.oos)})")
        print(f"ML accuracy:         {report.ml.overall_accuracy:.1%} (n={len(report.ml.oos)})")
        print(f"Baseline always-up:  {report.baseline_always_up.overall_accuracy:.1%}")
        print(f"Baseline prev-day:   {report.baseline_previous_day.overall_accuracy:.1%}")
    print(f"\nSaved full report to {out_path}")
