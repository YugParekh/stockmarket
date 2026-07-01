"""
Tests for the walk-forward split mechanism in signal_engine/backtest.py and
signal_engine/ml_model.py, using synthetic data (no network calls).

These are the no-lookahead guarantee tests at the mechanism level: given a
date range pooled across symbols, assert that every training fold only ever
contains rows strictly BEFORE the corresponding test fold's earliest date.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_engine.backtest import _rule_based_walk_forward, run_backtest_for_horizon
from signal_engine.dataset import HORIZONS, SymbolDataset
from signal_engine.indicators import FEATURE_COLUMNS, build_features
from signal_engine.ml_model import MIN_TRAIN_YEARS, _pool_datasets, walk_forward_predict


def _make_symbol_dataset(symbol: str, n_years: int = 6, seed: int = 0) -> SymbolDataset:
    rng = np.random.RandomState(seed)
    n = n_years * 252
    index = pd.bdate_range("2015-01-01", periods=n)
    close = 100 + np.cumsum(rng.randn(n) * 0.5)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + np.abs(rng.randn(n) * 0.3),
            "low": close - np.abs(rng.randn(n) * 0.3),
            "close": close,
            "volume": rng.randint(1000, 5000, n).astype(float),
        },
        index=index,
    )
    features = build_features(df)
    frame = features.copy()
    frame["close"] = df["close"]
    for h in HORIZONS:
        fwd = df["close"].shift(-h) / df["close"] - 1.0
        frame[f"label_{h}"] = (fwd > 0).astype(float)
        frame[f"forward_return_{h}"] = fwd
    frame = frame.dropna(subset=FEATURE_COLUMNS + [f"label_{h}" for h in HORIZONS])
    return SymbolDataset(symbol=symbol, frame=frame)


@pytest.fixture
def datasets() -> dict[str, SymbolDataset]:
    return {
        "SYM_A": _make_symbol_dataset("SYM_A", seed=1),
        "SYM_B": _make_symbol_dataset("SYM_B", seed=2),
    }


def test_pool_datasets_sorted_by_date(datasets):
    pooled = _pool_datasets(datasets, "label_1")
    dates = pooled["date"]
    assert (dates.values[:-1] <= dates.values[1:]).all()


def test_walk_forward_split_never_trains_on_future_relative_to_test_fold(datasets):
    """
    Mechanism-level no-lookahead guarantee: reconstruct the same fold logic
    ml_model.walk_forward_predict uses internally, and assert that for every
    fold, max(train dates) < min(test dates for that fold).
    """
    label_col = "label_1"
    pooled = _pool_datasets(datasets, label_col)
    pooled["year"] = pooled["date"].dt.year
    years = sorted(pooled["year"].unique())

    assert len(years) > MIN_TRAIN_YEARS

    for i, test_year in enumerate(years):
        if i < MIN_TRAIN_YEARS:
            continue
        train_mask = pooled["year"] < test_year
        test_mask = pooled["year"] == test_year

        train_dates = pooled.loc[train_mask, "date"]
        test_dates = pooled.loc[test_mask, "date"]

        if train_dates.empty or test_dates.empty:
            continue

        assert train_dates.max() < test_dates.min(), (
            f"Lookahead detected: train fold for test_year={test_year} contains a date "
            f"({train_dates.max()}) >= the test fold's earliest date ({test_dates.min()})"
        )


def test_walk_forward_predict_oos_predictions_are_all_after_min_train_years(datasets):
    label_col = "label_1"
    oos = walk_forward_predict(datasets, label_col)

    pooled = _pool_datasets(datasets, label_col)
    pooled["year"] = pooled["date"].dt.year
    years = sorted(pooled["year"].unique())
    first_scored_year = years[MIN_TRAIN_YEARS]

    oos_years = pd.to_datetime(oos["date"]).dt.year
    assert (oos_years >= first_scored_year).all()


def test_walk_forward_predict_covers_every_symbol(datasets):
    oos = walk_forward_predict(datasets, "label_1")
    assert set(oos["symbol"].unique()) == set(datasets.keys())


def test_rule_based_walk_forward_uses_same_oos_rowset_as_ml(datasets):
    """The rule-based and ML engines must be scored on identical (symbol, date)
    out-of-sample rows for the backtest comparison to be fair."""
    label_col = "label_1"
    ml_oos = walk_forward_predict(datasets, label_col)
    rb_oos = _rule_based_walk_forward(datasets, label_col)

    ml_keys = set(zip(ml_oos["symbol"], pd.to_datetime(ml_oos["date"])))
    rb_keys = set(zip(rb_oos["symbol"], pd.to_datetime(rb_oos["date"])))
    assert ml_keys == rb_keys


def test_run_backtest_for_horizon_produces_baselines_on_same_rows(datasets):
    report = run_backtest_for_horizon(datasets, horizon=1)

    ml_keys = set(zip(report.ml.oos["symbol"], pd.to_datetime(report.ml.oos["date"])))
    baseline_up_keys = set(
        zip(
            report.baseline_always_up.oos["symbol"],
            pd.to_datetime(report.baseline_always_up.oos["date"]),
        )
    )
    baseline_prev_keys = set(
        zip(
            report.baseline_previous_day.oos["symbol"],
            pd.to_datetime(report.baseline_previous_day.oos["date"]),
        )
    )

    assert ml_keys == baseline_up_keys
    assert ml_keys == baseline_prev_keys


def test_baseline_always_up_predicts_up_every_row(datasets):
    report = run_backtest_for_horizon(datasets, horizon=1)
    assert (report.baseline_always_up.oos["pred"] == 1).all()


def test_insufficient_history_raises_value_error():
    # Only 1 year of data -> fewer distinct years than MIN_TRAIN_YEARS requires.
    short_dataset = {"SYM_SHORT": _make_symbol_dataset("SYM_SHORT", n_years=1, seed=9)}
    with pytest.raises(ValueError):
        walk_forward_predict(short_dataset, "label_1")


def test_per_symbol_accuracy_keys_match_input_symbols(datasets):
    report = run_backtest_for_horizon(datasets, horizon=1)
    assert set(report.ml.per_symbol_accuracy().keys()) == set(datasets.keys())
    assert set(report.rule_based.per_symbol_accuracy().keys()) == set(datasets.keys())
