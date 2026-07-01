"""
Trains and persists the model actually served by backend/main.py.

This is deliberately separate from backtest.py: backtest.py measures HONEST
out-of-sample accuracy via walk-forward validation (never trains on the future
relative to what it's scoring). This script does two things with that same
walk-forward machinery:

1. Runs the walk-forward backtest for the 1-day horizon to get a calibration
   table from genuine historical out-of-sample predictions (never recomputed
   from an in-sample fit — that would produce a dishonestly optimistic
   calibration).
2. Fits ONE final model on ALL available historical data (no holdout) for
   live serving — there is no "future" left to leak from at serving time, so
   using every available data point is correct here, unlike in the backtest.

Run this whenever the underlying data or model has meaningfully changed:

    cd backend && source .venv/bin/activate && python -m signal_engine.train_production_model

Outputs (committed to git — the live API loads these directly, no training
step happens at request time or at deploy time):
    signal_engine/artifacts/model_1day.joblib
    signal_engine/artifacts/calibration_1day.json
    signal_engine/artifacts/metadata.json
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib

from signal_engine.calibration import fit_calibration
from signal_engine.dataset import DEFAULT_SYMBOLS, build_all_datasets
from signal_engine.ml_model import fit_final_model, walk_forward_predict

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

HORIZON = 1  # matches the dashboard's "next 1-3 sessions" prediction language
LABEL_COL = f"label_{HORIZON}"


def main() -> None:
    print(f"Building datasets for {DEFAULT_SYMBOLS} ...")
    datasets = build_all_datasets(DEFAULT_SYMBOLS, period="8y")
    failed = [s for s in DEFAULT_SYMBOLS if s not in datasets]
    if failed:
        print(f"WARNING: failed to fetch {failed}, proceeding without them")

    print("Running walk-forward backtest for an honest calibration table ...")
    oos = walk_forward_predict(datasets, LABEL_COL)
    calibration = fit_calibration(oos["proba_up"], oos["label"])
    print(f"Out-of-sample accuracy used for calibration: {calibration.overall_accuracy:.1%} (n={calibration.n})")

    print("Fitting final production model on ALL available history ...")
    model = fit_final_model(datasets, LABEL_COL)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS_DIR / "model_1day.joblib"
    calibration_path = ARTIFACTS_DIR / "calibration_1day.json"
    metadata_path = ARTIFACTS_DIR / "metadata.json"

    joblib.dump(model, model_path)
    calibration_path.write_text(json.dumps(calibration.to_dict(), indent=2))
    metadata_path.write_text(
        json.dumps(
            {
                "horizon_days": HORIZON,
                "symbols_trained_on": sorted(datasets.keys()),
                "symbols_failed": failed,
                "n_training_rows": int(sum(len(ds.frame) for ds in datasets.values())),
                "backtest_overall_accuracy": calibration.overall_accuracy,
                "ship_to_production": False,
                "note": (
                    "SHIP_TO_PRODUCTION is False in signal_engine/registry.py: this model "
                    "does not beat the naive 'always predict UP' baseline in backtesting. "
                    "It is served with honest, capped confidence, not as a strong signal. "
                    "See signal_engine/README.md for the full backtest report."
                ),
            },
            indent=2,
        )
    )
    print(f"Saved model to {model_path}")
    print(f"Saved calibration to {calibration_path}")
    print(f"Saved metadata to {metadata_path}")


if __name__ == "__main__":
    main()
