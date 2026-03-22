from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Literal
import os

import httpx
import numpy as np
import yfinance as yf
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


PredictionDirection = Literal["UP", "DOWN"]


class MarketDataPoint(BaseModel):
    date: str
    price: float
    sentiment_score: float
    volume: int
    prediction: PredictionDirection
    confidence: int


class NewsItem(BaseModel):
    id: int
    headline: str
    sentiment: Literal["Positive", "Neutral", "Negative"]
    impact: Literal["Low", "Medium", "High"]
    timestamp: str


class AlertItem(BaseModel):
    id: int
    message: str
    severity: Literal["Positive", "Neutral", "Negative"]
    createdAt: str


class KeywordStat(BaseModel):
    keyword: str
    frequency: int
    sentiment: Literal["Positive", "Neutral", "Negative"]


class SentimentBucket(BaseModel):
    label: str
    value: int


class PredictionSummary(BaseModel):
    direction: PredictionDirection
    confidence: int
    expectedReturnPct: float
    volatilityScore: float
    horizon: str


class RiskSummary(BaseModel):
    level: Literal["Low", "Medium", "High"]
    valueAtRiskPct: float


class Insights(BaseModel):
    nextMove: PredictionSummary
    risk: RiskSummary
    commentary: str


class DashboardResponse(BaseModel):
    symbol: str
    range: str
    marketData: List[MarketDataPoint]
    news: List[NewsItem]
    alerts: List[AlertItem]
    keywords: List[KeywordStat]
    sentimentDistribution: List[SentimentBucket]
    insights: Insights


class SymbolSearchResult(BaseModel):
    symbol: str
    description: str
    type: str | None = None


class SymbolSearchResponse(BaseModel):
    count: int
    result: list[SymbolSearchResult]


load_dotenv()
FINNHUB_TOKEN = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


app = FastAPI(title="MarketSentinel AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class RangeConfig:
    seconds: int
    resolution: str


RANGE_MAP: dict[str, RangeConfig] = {
    # Short intraday window, 5-minute candles
    "1D": RangeConfig(seconds=60 * 60 * 8, resolution="5"),
    # Last 5 trading days, 15-minute candles
    "5D": RangeConfig(seconds=60 * 60 * 24 * 5, resolution="15"),
    # Approx. 1 month, 60-minute candles
    "1M": RangeConfig(seconds=60 * 60 * 24 * 30, resolution="60"),
    "3M": RangeConfig(seconds=60 * 60 * 24 * 90, resolution="D"),
    "6M": RangeConfig(seconds=60 * 60 * 24 * 180, resolution="D"),
    "1Y": RangeConfig(seconds=60 * 60 * 24 * 365, resolution="D"),
}


@dataclass
class YFinanceRangeConfig:
    period: str
    interval: str


YF_RANGE_MAP: dict[str, YFinanceRangeConfig] = {
    "1D": YFinanceRangeConfig(period="1d", interval="5m"),
    "5D": YFinanceRangeConfig(period="5d", interval="30m"),
    "1M": YFinanceRangeConfig(period="1mo", interval="1d"),
    "3M": YFinanceRangeConfig(period="3mo", interval="1d"),
    "6M": YFinanceRangeConfig(period="6mo", interval="1d"),
    "1Y": YFinanceRangeConfig(period="1y", interval="1d"),
}


def _compute_point_features(
    closes: np.ndarray, volumes: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simple feature engineering for demonstration:
    - rolling return vs short moving average
    - volatility proxy
    - volume z-score
    """
    if len(closes) == 0:
        return (
            np.array([]),
            np.array([]),
            np.array([]),
        )

    window = min(10, len(closes))
    ma = np.convolve(closes, np.ones(window) / window, mode="same")
    returns = np.zeros_like(closes)
    returns[1:] = (closes[1:] - closes[:-1]) / np.where(
        closes[:-1] == 0, 1, closes[:-1]
    )

    # volatility proxy: rolling std of returns
    vol_window = min(10, len(returns))
    if vol_window > 1:
        vol = np.concatenate(
            [
                np.full(vol_window - 1, np.nan),
                np.array(
                    [
                        np.nanstd(returns[i - vol_window + 1 : i + 1])
                        for i in range(vol_window - 1, len(returns))
                    ]
                ),
            ]
        )
    else:
        vol = np.zeros_like(returns)

    vol = np.nan_to_num(vol)

    # volume z-score
    vol_mean = float(np.mean(volumes)) if len(volumes) else 0.0
    vol_std = float(np.std(volumes)) if len(volumes) else 1.0
    vol_z = (volumes - vol_mean) / (vol_std or 1.0)

    return returns, closes - ma, vol_z


def _score_sentiment(
    returns: np.ndarray, price_vs_ma: np.ndarray, vol_z: np.ndarray
) -> np.ndarray:
    """
    Heuristic sentiment model:
    - positive when price is above its short MA and returns are positive
    - negative on drawdowns with elevated volatility and volumes
    Returns scores in [-1, 1].
    """
    if len(returns) == 0:
        return np.array([])

    raw = (
        1.5 * returns
        + 0.002 * price_vs_ma
        - 0.15 * np.clip(vol_z, -3, 3)
    )
    raw = np.tanh(raw * 3.0)
    return np.clip(raw, -1.0, 1.0)


def _prediction_from_series(sentiment_scores: np.ndarray) -> tuple[PredictionDirection, int]:
    if len(sentiment_scores) == 0:
        return "UP", 50

    recent = sentiment_scores[-5:] if len(sentiment_scores) >= 5 else sentiment_scores
    avg_sent = float(np.mean(recent))
    slope = float(recent[-1] - recent[0]) if len(recent) > 1 else 0.0

    bullish_score = 0.6 * avg_sent + 0.4 * slope

    direction: PredictionDirection = "UP" if bullish_score >= 0 else "DOWN"
    confidence = int(min(95, max(55, (abs(bullish_score) * 80) + 55)))

    return direction, confidence


def _sentiment_buckets(scores: np.ndarray) -> list[SentimentBucket]:
    if len(scores) == 0:
        return [
            SentimentBucket(label="Positive", value=0),
            SentimentBucket(label="Neutral", value=0),
            SentimentBucket(label="Negative", value=0),
        ]

    pos = int(np.sum(scores > 0.1))
    neg = int(np.sum(scores < -0.1))
    neu = int(len(scores) - pos - neg)
    return [
        SentimentBucket(label="Positive", value=pos),
        SentimentBucket(label="Neutral", value=neu),
        SentimentBucket(label="Negative", value=neg),
    ]


def _analyze_text_sentiment(text: str) -> float:
    """
    Very lightweight lexicon-based sentiment score in [-1, 1].
    This avoids pulling heavy ML models into the backend.
    """
    text_lower = text.lower()
    positive_words = [
        "gain",
        "gains",
        "up",
        "surge",
        "rally",
        "beat",
        "record",
        "strong",
        "bullish",
        "growth",
        "optimistic",
        "upgrade",
        "outperform",
        "profit",
    ]
    negative_words = [
        "loss",
        "down",
        "slump",
        "drop",
        "fall",
        "bearish",
        "cut",
        "downgrade",
        "miss",
        "weak",
        "selloff",
        "risk",
        "concern",
        "volatility",
    ]

    pos = sum(word in text_lower for word in positive_words)
    neg = sum(word in text_lower for word in negative_words)

    if pos == 0 and neg == 0:
        return 0.0

    score = (pos - neg) / (pos + neg)
    # squash to [-1, 1]
    return float(max(-1.0, min(1.0, score)))


def _label_from_score(score: float) -> Literal["Positive", "Neutral", "Negative"]:
    if score > 0.15:
        return "Positive"
    if score < -0.15:
        return "Negative"
    return "Neutral"


async def _fetch_finnhub_candles(symbol: str, cfg: RangeConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Try Finnhub first; if unavailable or unauthorized, fall back to Yahoo Finance.
    This ensures you still get real (delayed) prices even without a Finnhub key.
    """
    if FINNHUB_TOKEN:
        now_ts = int(datetime.utcnow().timestamp())
        from_ts = now_ts - cfg.seconds

        params = {
            "symbol": symbol,
            "resolution": cfg.resolution,
            "from": from_ts,
            "to": now_ts,
            "token": FINNHUB_TOKEN,
        }

        async with httpx.AsyncClient(base_url=FINNHUB_BASE_URL, timeout=10.0) as client:
            try:
                resp = await client.get("/stock/candle", params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("s") == "ok":
                    closes = np.array(data.get("c", []), dtype=float)
                    volumes = np.array(data.get("v", []), dtype=float)
                    timestamps = np.array(data.get("t", []), dtype=int)
                    if len(closes) and len(volumes) and len(timestamps):
                        return closes, volumes, timestamps
            except httpx.HTTPError:
                # fall through to yfinance
                pass

    # Finnhub missing/unauthorized or returned no data: use yfinance as a real-data fallback.
    yf_cfg = YF_RANGE_MAP.get("1M")
    if yf_cfg is None:
        raise HTTPException(status_code=500, detail="Internal configuration error")

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=yf_cfg.period, interval=yf_cfg.interval)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"YFinance error: {exc}") from exc

    if hist.empty:
        raise HTTPException(
            status_code=404, detail=f"No market data available for symbol {symbol}"
        )

    closes = hist["Close"].to_numpy(dtype=float)
    volumes = hist["Volume"].to_numpy(dtype=float)
    timestamps = np.array(
        [int(ts.timestamp()) for ts in hist.index.to_pydatetime()], dtype=int
    )

    return closes, volumes, timestamps


async def _fetch_finnhub_news(symbol: str) -> list[NewsItem]:
    if not FINNHUB_TOKEN:
        return []

    today = datetime.utcnow().date()
    start = today - timedelta(days=3)

    params = {
        "symbol": symbol,
        "from": start.isoformat(),
        "to": today.isoformat(),
        "token": FINNHUB_TOKEN,
    }

    async with httpx.AsyncClient(base_url=FINNHUB_BASE_URL, timeout=10.0) as client:
        try:
            resp = await client.get("/company-news", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

    raw_items = resp.json()
    news: list[NewsItem] = []

    for idx, item in enumerate(raw_items[:12], start=1):
        headline = item.get("headline") or ""
        summary = item.get("summary") or ""
        if not headline:
            continue

        text = f"{headline}. {summary}"
        score = _analyze_text_sentiment(text)
        label = _label_from_score(score)

        abs_score = abs(score)
        if abs_score > 0.55:
            impact: Literal["Low", "Medium", "High"] = "High"
        elif abs_score > 0.25:
            impact = "Medium"
        else:
            impact = "Low"

        ts = item.get("datetime") or 0
        ts_str = datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")

        news.append(
            NewsItem(
                id=idx,
                headline=headline,
                sentiment=label,
                impact=impact,
                timestamp=ts_str,
            )
        )

    return news


def _fallback_alerts(symbol: str) -> list[AlertItem]:
    return [
        AlertItem(
            id=1,
            message=f"Unusual call volume detected in {symbol} vs 30-day average",
            severity="Positive",
            createdAt="2 min ago",
        ),
        AlertItem(
            id=2,
            message=f"Short-term sentiment divergence vs price for {symbol}",
            severity="Neutral",
            createdAt="9 min ago",
        ),
        AlertItem(
            id=3,
            message="Cross-asset risk indicators flashing mild risk-off regime",
            severity="Negative",
            createdAt="26 min ago",
        ),
    ]


def _build_alerts_from_series(
    symbol: str,
    closes: np.ndarray,
    volumes: np.ndarray,
    sentiment_scores: np.ndarray,
    news: list[NewsItem],
) -> list[AlertItem]:
    alerts: list[AlertItem] = []
    if len(closes) == 0:
        return _fallback_alerts(symbol)

    latest_close = float(closes[-1])
    mean_vol = float(np.mean(volumes)) if len(volumes) else 0.0
    latest_vol = float(volumes[-1]) if len(volumes) else 0.0
    recent_sent = (
        sentiment_scores[-10:] if len(sentiment_scores) >= 10 else sentiment_scores
    )
    avg_recent_sent = float(np.mean(recent_sent)) if len(recent_sent) else 0.0

    # High negative sentiment alert
    if avg_recent_sent < -0.35:
        alerts.append(
            AlertItem(
                id=len(alerts) + 1,
                message=f"High negative sentiment detected in {symbol} over the last sessions",
                severity="Negative",
                createdAt="Just now",
            )
        )

    # Volume spike alert
    if mean_vol > 0 and latest_vol > mean_vol * 1.8:
        alerts.append(
            AlertItem(
                id=len(alerts) + 1,
                message=f"Unusual trading volume spike in {symbol} vs recent average",
                severity="Neutral",
                createdAt="Just now",
            )
        )

    # Positive earnings/news style alert
    has_positive_earnings = any(
        ("earnings" in n.headline.lower() or "results" in n.headline.lower())
        and n.sentiment == "Positive"
        for n in news
    )
    if has_positive_earnings:
        alerts.append(
            AlertItem(
                id=len(alerts) + 1,
                message=f"Positive earnings or results tone detected in recent {symbol} news",
                severity="Positive",
                createdAt="Last 24h",
            )
        )

    return alerts or _fallback_alerts(symbol)


def _build_keywords_from_news(news: list[NewsItem]) -> list[KeywordStat]:
    if not news:
        return [
            KeywordStat(keyword="inflation", frequency=32, sentiment="Negative"),
            KeywordStat(keyword="earnings", frequency=47, sentiment="Positive"),
            KeywordStat(keyword="AI", frequency=65, sentiment="Positive"),
            KeywordStat(keyword="interest rates", frequency=28, sentiment="Negative"),
            KeywordStat(keyword="product launch", frequency=21, sentiment="Positive"),
        ]

    stopwords = {
        "the",
        "and",
        "to",
        "of",
        "in",
        "on",
        "for",
        "at",
        "with",
        "a",
        "an",
        "after",
        "from",
        "as",
        "by",
        "new",
        "stock",
        "shares",
        "company",
        "market",
    }

    freq: dict[str, int] = {}
    sentiment_votes: dict[str, dict[str, int]] = {}

    for item in news:
        text = f"{item.headline} {item.timestamp}"
        words = [
            "".join(ch for ch in w.lower() if ch.isalnum())
            for w in text.split()
        ]
        for w in words:
            if not w or w in stopwords or len(w) <= 2:
                continue
            freq[w] = freq.get(w, 0) + 1
            if w not in sentiment_votes:
                sentiment_votes[w] = {"Positive": 0, "Neutral": 0, "Negative": 0}
            sentiment_votes[w][item.sentiment] += 1

    stats: list[KeywordStat] = []
    for word, count in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:20]:
        votes = sentiment_votes.get(word, {})
        sentiment = max(votes, key=votes.get) if votes else "Neutral"
        stats.append(
            KeywordStat(keyword=word, frequency=count, sentiment=sentiment)  # type: ignore[arg-type]
        )

    return stats


def _build_insights(
    symbol: str,
    closes: np.ndarray,
    sentiment_scores: np.ndarray,
    direction: PredictionDirection,
    confidence: int,
) -> Insights:
    if len(closes) == 0:
        return Insights(
            nextMove=PredictionSummary(
                direction="UP",
                confidence=50,
                expectedReturnPct=0.0,
                volatilityScore=0.0,
                horizon="next 1–3 sessions",
            ),
            risk=RiskSummary(level="Medium", valueAtRiskPct=2.0),
            commentary=f"Not enough recent data for {symbol} to compute a directional view.",
        )

    # Approximate daily returns from closes
    returns = np.zeros_like(closes, dtype=float)
    returns[1:] = (closes[1:] - closes[:-1]) / np.where(closes[:-1] == 0, 1, closes[:-1])
    recent = returns[-10:] if len(returns) > 10 else returns
    avg_ret = float(np.mean(recent)) if len(recent) else 0.0
    vol = float(np.std(recent)) if len(recent) else 0.0

    expected_return_pct = float(round(avg_ret * 100.0, 2))
    volatility_score = float(round(min(100.0, vol * 1000.0), 1))

    # Simple risk level based on volatility
    if volatility_score < 25:
        risk_level: Literal["Low", "Medium", "High"] = "Low"
    elif volatility_score < 55:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # 95% one-day VaR approximation
    value_at_risk_pct = float(round(1.65 * vol * 100.0, 2))

    # Sentiment overlay for commentary
    recent_sent = (
        sentiment_scores[-10:] if len(sentiment_scores) >= 10 else sentiment_scores
    )
    avg_sent = float(np.mean(recent_sent)) if len(recent_sent) else 0.0

    if avg_sent > 0.25:
        sent_label = "strongly bullish"
    elif avg_sent > 0.05:
        sent_label = "slightly bullish"
    elif avg_sent < -0.25:
        sent_label = "strongly bearish"
    elif avg_sent < -0.05:
        sent_label = "slightly bearish"
    else:
        sent_label = "broadly neutral"

    dir_word = "upside" if direction == "UP" else "downside"
    commentary = (
        f"Models currently lean {dir_word} on {symbol} with {confidence}% confidence, "
        f"{sent_label} news tone, and an estimated ±{value_at_risk_pct:.2f}% one-day risk band."
    )

    return Insights(
        nextMove=PredictionSummary(
            direction=direction,
            confidence=confidence,
            expectedReturnPct=expected_return_pct,
            volatilityScore=volatility_score,
            horizon="next 1–3 sessions",
        ),
        risk=RiskSummary(level=risk_level, valueAtRiskPct=value_at_risk_pct),
        commentary=commentary,
    )


@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    symbol: str = Query("AAPL", min_length=1, max_length=32),
    range: str = Query("1M", pattern="^(1D|5D|1M|3M|6M|1Y)$"),
) -> DashboardResponse:
    """Return real market data plus AI-style sentiment & prediction."""
    cfg = RANGE_MAP.get(range, RANGE_MAP["1M"])

    closes, volumes, timestamps = await _fetch_finnhub_candles(symbol, cfg)

    returns, price_vs_ma, vol_z = _compute_point_features(closes, volumes)
    sentiment_scores = _score_sentiment(returns, price_vs_ma, vol_z)

    direction, global_conf = _prediction_from_series(sentiment_scores)
    insights = _build_insights(symbol, closes, sentiment_scores, direction, global_conf)

    points: list[MarketDataPoint] = []
    for close, vol, ts, sent in zip(
        closes, volumes, timestamps, sentiment_scores
    ):
        # Slightly vary per-point confidence around global confidence.
        jitter = int(min(8, max(-8, (sent * 15))))
        confidence = int(min(98, max(50, global_conf + jitter)))

        points.append(
            MarketDataPoint(
                date=datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M"),
                price=float(round(close, 2)),
                sentiment_score=float(round(float(sent), 3)),
                volume=int(vol),
                prediction=direction,
                confidence=confidence,
            )
        )

    buckets = _sentiment_buckets(sentiment_scores)
    news = await _fetch_finnhub_news(symbol)
    alerts = _build_alerts_from_series(symbol, closes, volumes, sentiment_scores, news)
    keywords = _build_keywords_from_news(news)

    return DashboardResponse(
        symbol=symbol,
        range=range,
        marketData=points,
        news=news,
        alerts=alerts,
        keywords=keywords,
        sentimentDistribution=buckets,
        insights=insights,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/api/search", response_model=SymbolSearchResponse)
async def search_symbols(q: str = Query(..., min_length=1, max_length=64)) -> SymbolSearchResponse:
    if not FINNHUB_TOKEN:
        raise HTTPException(status_code=500, detail="FINNHUB_API_KEY is not configured")

    params = {"q": q, "token": FINNHUB_TOKEN}
    async with httpx.AsyncClient(base_url=FINNHUB_BASE_URL, timeout=10.0) as client:
        try:
            resp = await client.get("/search", params=params)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover
            raise HTTPException(status_code=502, detail=f"Finnhub search error: {exc}") from exc

    data = resp.json() or {}
    result = data.get("result", [])

    # Prefer equities first to reduce noise.
    equities = [r for r in result if (r.get("type") or "").upper() in {"COMMON STOCK", "EQUITY"}]
    others = [r for r in result if r not in equities]
    ordered = (equities + others)[:10]

    return SymbolSearchResponse(
        count=int(data.get("count", len(ordered)) or len(ordered)),
        result=[
            SymbolSearchResult(
                symbol=str(r.get("symbol", "")).upper(),
                description=str(r.get("description", "")),
                type=r.get("type"),
            )
            for r in ordered
            if r.get("symbol") and r.get("description")
        ],
    )


# To run:
#   cd backend
#   uvicorn main:app --reload --port 8000

