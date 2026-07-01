"""
Deterministic unit tests for signal_engine/calibration.py using synthetic
(predicted_score, actual_outcome) pairs with a known bucket structure. No
network calls.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_engine.calibration import fit_calibration


def test_fit_calibration_perfect_predictor_yields_100pct_buckets():
    # proba_up perfectly agrees with label in every row -> every bucket should
    # show 100% accuracy, and overall accuracy should be exactly 1.0.
    n = 400
    rng = np.random.RandomState(0)
    label = pd.Series(rng.randint(0, 2, n))
    # proba_up strongly signals the true label: 0.9 when label==1, 0.1 when label==0.
    proba_up = label.map({1: 0.9, 0: 0.1})

    table = fit_calibration(proba_up, label, n_buckets=4)

    assert table.overall_accuracy == pytest.approx(1.0)
    assert table.n == n
    for bucket in table.buckets:
        assert bucket.accuracy == pytest.approx(1.0)


def test_fit_calibration_random_predictor_yields_near_50pct():
    n = 2000
    rng = np.random.RandomState(1)
    label = pd.Series(rng.randint(0, 2, n))
    # proba_up carries no information about label at all.
    proba_up = pd.Series(rng.uniform(0.0, 1.0, n))

    table = fit_calibration(proba_up, label, n_buckets=5)

    assert table.overall_accuracy == pytest.approx(0.5, abs=0.05)


def test_fit_calibration_known_two_bucket_structure():
    """
    Construct an explicit dataset with two known regimes:
      - "weak" predictions (proba_up close to 0.5): correct only 50% of the time.
      - "strong" predictions (proba_up far from 0.5): correct 90% of the time.
    Verify the resulting bucket table recovers approximately these two accuracy
    levels, and that stronger predictions land in a bucket with higher accuracy
    (this is what calibration is supposed to prove and expose).
    """
    rng = np.random.RandomState(42)
    n_weak, n_strong = 1000, 1000

    weak_proba = pd.Series(0.5 + rng.uniform(-0.02, 0.02, n_weak))
    weak_label = pd.Series(rng.randint(0, 2, n_weak))  # unrelated to weak_proba -> ~50%

    strong_proba_up_side = pd.Series(0.9 + rng.uniform(-0.02, 0.02, n_strong // 2))
    strong_label_up_side = pd.Series((rng.uniform(0, 1, n_strong // 2) < 0.9).astype(int))
    strong_proba_down_side = pd.Series(0.1 + rng.uniform(-0.02, 0.02, n_strong // 2))
    strong_label_down_side = pd.Series((rng.uniform(0, 1, n_strong // 2) < 0.1).astype(int))

    proba_up = pd.concat(
        [weak_proba, strong_proba_up_side, strong_proba_down_side], ignore_index=True
    )
    label = pd.concat(
        [weak_label, strong_label_up_side, strong_label_down_side], ignore_index=True
    )

    table = fit_calibration(proba_up, label, n_buckets=2)

    assert len(table.buckets) == 2
    weakest_bucket = table.buckets[0]
    strongest_bucket = table.buckets[-1]

    # Weakest-strength bucket should be near chance; strongest should be well above it.
    assert weakest_bucket.accuracy == pytest.approx(0.5, abs=0.08)
    assert strongest_bucket.accuracy > weakest_bucket.accuracy
    assert strongest_bucket.accuracy == pytest.approx(0.9, abs=0.08)


def test_confidence_for_returns_bucket_accuracy_as_percent():
    n = 1000
    rng = np.random.RandomState(3)
    label = pd.Series(rng.randint(0, 2, n))
    proba_up = label.map({1: 0.85, 0: 0.15})

    table = fit_calibration(proba_up, label, n_buckets=3)

    confidence = table.confidence_for(0.85)
    assert isinstance(confidence, int)
    assert 0 <= confidence <= 100
    # Since proba_up perfectly predicts label here, confidence should be very high.
    assert confidence >= 90


def test_confidence_for_extreme_score_falls_back_to_last_bucket():
    n = 500
    rng = np.random.RandomState(4)
    label = pd.Series(rng.randint(0, 2, n))
    proba_up = pd.Series(rng.uniform(0.4, 0.6, n))  # never very extreme

    table = fit_calibration(proba_up, label, n_buckets=4)

    # A far more extreme score than anything observed in training should not crash,
    # and should fall back to the most extreme observed bucket's accuracy.
    confidence = table.confidence_for(0.999)
    assert 0 <= confidence <= 100
    assert confidence == int(round(table.buckets[-1].accuracy * 100))


def test_fit_calibration_empty_buckets_param_still_produces_valid_table():
    n = 100
    rng = np.random.RandomState(5)
    label = pd.Series(rng.randint(0, 2, n))
    proba_up = pd.Series(rng.uniform(0, 1, n))

    table = fit_calibration(proba_up, label, n_buckets=10)
    assert table.n == n
    assert sum(b.n for b in table.buckets) == n
