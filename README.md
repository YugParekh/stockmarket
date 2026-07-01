# MarketSentinel AI

A stock market analytics dashboard: real price data (Finnhub, falling back to Yahoo Finance),
sentiment scoring, and a backtested ML signal engine with honestly calibrated confidence. This
is an analytics/signals tool — it does not place trades or manage a portfolio.

- `backend/` — FastAPI service (Python): market data, signal engine, AI insights (Gemini)
- `src/` — React 18 + TypeScript + Vite + Tailwind + Recharts frontend

## Features

- **Real-time market data** — live price action via Finnhub, yfinance fallback
- **Backtested signal engine** — technical indicators + ML, walk-forward validated, confidence
  calibrated from real historical accuracy (see `backend/signal_engine/README.md`)
- **AI insights & Q&A** — Gemini-powered deep analysis and chat grounded in real dashboard data
  (`backend/ai_insights.py`), plus a client-side Hugging Face sentiment integration (`src/api/ai.ts`)
- **News intelligence** — curated headlines with per-item sentiment/impact scoring
- **CSV export**, custom `useMarketData` polling hook, and a glassmorphism/neon-glow UI

This project is being evolved into a multi-user platform with authentication, persisted
watchlists, background data ingestion, and a versioned/backtestable signal engine. See
`.claude/plans/` for the current roadmap if present, or ask for the latest status.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # or requirements.txt for prod-only deps
cp .env.example .env                  # then fill in FINNHUB_API_KEY, optionally GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

Run tests:

```bash
cd backend
source .venv/bin/activate
pytest tests/
```

### Required environment variables (`backend/.env`)

| Variable | Purpose | Required |
|---|---|---|
| `FINNHUB_API_KEY` | Real-time candles, news, symbol search via Finnhub | No — falls back to yfinance (price data only, no news/search) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of frontend origins allowed to call the API | No — defaults to `http://localhost:5173` |
| `GEMINI_API_KEY` | Powers `/api/ai-insights` and `/api/ai-chat` (free tier: aistudio.google.com/apikey) | No — those two endpoints return `configured: false` and the rest of the app works normally |

**Security note:** if you have a Finnhub key that was ever stored in a plaintext `.env` file or
pasted anywhere outside a secrets manager, rotate it in the Finnhub dashboard and update it only
via your deployment platform's environment variable settings — never commit it to a file tracked
by git.

## Frontend setup

```bash
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8000
npm run build    # production build to dist/
```

By default the frontend calls a hardcoded production backend URL
(see `src/api/dashboard.ts` / `src/api/search.ts`). For local development against your own
backend, update `BASE_URL` in those files or run the backend locally on port 8000 and use the
Vite dev proxy configured in `vite.config.ts`.

**Note on `src/api/ai.ts`:** this calls the Hugging Face Inference API directly from the browser
using `VITE_HF_API_TOKEN`. Vite bundles `VITE_`-prefixed env vars into the public client-side JS
— that token is visible to anyone who inspects the deployed site. Treat it as a low-privilege,
rotatable key, not a secret.

## Deployment

Both services are currently deployed on Render:
- Backend: set `FINNHUB_API_KEY`, `CORS_ALLOWED_ORIGINS` (include your deployed frontend URL),
  and optionally `GEMINI_API_KEY` as environment variables in the Render dashboard — never in a
  committed file.
- Frontend: standard Vite static build (`npm run build`, serve `dist/`).
