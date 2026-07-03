"""
Environment-driven configuration and the persisted ML model artifacts, loaded
once at import time and shared across services/routers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
from dotenv import load_dotenv

from signal_engine.calibration import CalibrationTable

load_dotenv()

FINNHUB_TOKEN = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Comma-separated list of allowed frontend origins, e.g.
# "http://localhost:5173,https://your-frontend.onrender.com"
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Backtested, calibration-validated 1-day direction model (see signal_engine/README.md).
# SHIP_TO_PRODUCTION is False in signal_engine/registry.py — it does not beat a naive
# "always predict UP" baseline — so it is served with honest, calibration-capped
# confidence (typically 45-58%) rather than presented as a strong trading signal.
# Loaded once at import time; falls back to the older heuristic if artifacts are
# missing (e.g. before `python -m signal_engine.train_production_model` has been run).
_ML_ARTIFACTS_DIR = Path(__file__).parent.parent / "signal_engine" / "artifacts"
try:
    ML_MODEL = joblib.load(_ML_ARTIFACTS_DIR / "model_1day.joblib")
    ML_CALIBRATION = CalibrationTable.from_dict(
        json.loads((_ML_ARTIFACTS_DIR / "calibration_1day.json").read_text())
    )
except FileNotFoundError:
    ML_MODEL = None
    ML_CALIBRATION = None
