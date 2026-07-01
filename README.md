# MarketSentinel AI

A stock market analytics dashboard: real price data (Finnhub, falling back to Yahoo Finance),
heuristic sentiment scoring, and rule-based directional predictions. This is an
analytics/signals tool — it does not place trades or manage a portfolio.

- `backend/` — FastAPI service (Python)
- `src/` — React 18 + TypeScript + Vite + Tailwind + Recharts frontend

This project is being evolved into a multi-user platform with authentication, persisted
watchlists, background data ingestion, and a versioned/backtestable signal engine. See
`.claude/plans/` for the current roadmap if present, or ask for the latest status.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # or requirements.txt for prod-only deps
cp .env.example .env                  # then fill in FINNHUB_API_KEY
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

## Deployment

Both services are currently deployed on Render:
- Backend: set `FINNHUB_API_KEY` and `CORS_ALLOWED_ORIGINS` (include your deployed frontend URL)
  as environment variables in the Render dashboard — never in a committed file.
- Frontend: standard Vite static build (`npm run build`, serve `dist/`).
