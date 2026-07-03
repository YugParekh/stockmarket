"""
MarketSentinel AI backend — FastAPI app factory.

This file only wires the app together (CORS + routers). The actual logic
lives in services/ (business logic, data fetching) and routers/ (thin HTTP
layer). See backend/signal_engine/README.md for the ML prediction model and
backend/ai_insights.py for the Gemini-powered insights/chat feature.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import CORS_ALLOWED_ORIGINS
from routers import ai, dashboard, health, quotes, search

app = FastAPI(title="MarketSentinel AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(search.router)
app.include_router(quotes.router)
app.include_router(ai.router)


# To run:
#   cd backend
#   uvicorn main:app --reload --port 8000
