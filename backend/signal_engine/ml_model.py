"""
Walk-forward ML classifier: predicts forward-direction probability from the same
technical-indicator features used by the rule-based model, so the two can be compared
fairly on identical backtest splits.

Walk-forward protocol (no lookahead): data is pooled across symbols and sorted by date.
The model is retrained once per calendar year using only data strictly before that year,
then used to predict every row within that year. This mirrors how the model would
actually have been used in production — retrained periodically on the past, never on
the future relative to what it's predicting.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from signal_engine.dataset import SymbolDataset
from signal_engine.indicators import FEATURE_COLUMNS

MIN_TRAIN_YEARS = 2


def _pool_datasets(datasets: dict[str, SymbolDataset], label_col: str) -> pd.DataFrame:
    frames = []
    for symbol, ds in datasets.items():
        f = ds.frame[FEATURE_COLUMNS + [label_col]].copy()
        f.index = f.index.rename(None)
        f["symbol"] = symbol
        f["date"] = f.index
        frames.append(f)
    pooled = pd.concat(frames, axis=0)
    return pooled.sort_values("date").reset_index(drop=True)


def walk_forward_predict(
    datasets: dict[str, SymbolDataset], label_col: str
) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: symbol, date, proba_up, label — one row per
    out-of-sample prediction. Rows in years before MIN_TRAIN_YEARS of history exist are
    excluded (no valid training data yet).
    """
    pooled = _pool_datasets(datasets, label_col)
    pooled["year"] = pooled["date"].dt.year
    years = sorted(pooled["year"].unique())

    if len(years) <= MIN_TRAIN_YEARS:
        raise ValueError("Not enough distinct years of history for walk-forward validation")

    results = []
    for i, test_year in enumerate(years):
        if i < MIN_TRAIN_YEARS:
            continue  # not enough prior years to train on yet

        train_mask = pooled["year"] < test_year
        test_mask = pooled["year"] == test_year

        train_df = pooled.loc[train_mask]
        test_df = pooled.loc[test_mask]
        if train_df.empty or test_df.empty:
            continue

        model = HistGradientBoostingClassifier(
            max_depth=4,
            learning_rate=0.05,
            max_iter=150,
            random_state=42,
        )
        model.fit(train_df[FEATURE_COLUMNS], train_df[label_col])

        proba_up = model.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
        results.append(
            pd.DataFrame(
                {
                    "symbol": test_df["symbol"].values,
                    "date": test_df["date"].values,
                    "proba_up": proba_up,
                    "label": test_df[label_col].values,
                }
            )
        )

    if not results:
        raise ValueError("Walk-forward produced no out-of-sample predictions")

    return pd.concat(results, axis=0).sort_values("date").reset_index(drop=True)


def fit_final_model(
    datasets: dict[str, SymbolDataset], label_col: str
) -> HistGradientBoostingClassifier:
    """
    Trains on ALL available historical data (no holdout) — for production serving, not
    backtesting. The walk-forward split in `walk_forward_predict` exists to measure
    honest out-of-sample accuracy; once that accuracy has been measured and the decision
    is made to serve live predictions, the model that actually serves traffic should use
    every available data point, since there is no "future" left to leak from at serving
    time. Same hyperparameters as the walk-forward folds, for consistency with the
    backtested accuracy this model is expected to (approximately) match.
    """
    pooled = _pool_datasets(datasets, label_col)
    model = HistGradientBoostingClassifier(
        max_depth=4,
        learning_rate=0.05,
        max_iter=150,
        random_state=42,
    )
    model.fit(pooled[FEATURE_COLUMNS], pooled[label_col])
    return model
