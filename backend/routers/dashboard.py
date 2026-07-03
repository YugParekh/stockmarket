from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from schemas import DashboardResponse, MarketDataPoint
from services.insights import build_insights
from services.market_data import RANGE_MAP, fetch_daily_ohlcv_for_prediction, fetch_finnhub_candles
from services.news import build_alerts_from_series, build_keywords_from_news, fetch_finnhub_news
from services.prediction import ml_prediction, prediction_from_series
from services.sentiment import compute_point_features, score_sentiment, sentiment_buckets

router = APIRouter()


@router.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    symbol: str = Query("AAPL", min_length=1, max_length=32),
    range: str = Query("1M", pattern="^(1D|5D|1M|3M|6M|1Y)$"),
) -> DashboardResponse:
    """Return real market data plus AI-style sentiment & prediction."""
    cfg = RANGE_MAP.get(range, RANGE_MAP["1M"])

    closes, volumes, timestamps = await fetch_finnhub_candles(symbol, cfg)

    returns, price_vs_ma, vol_z = compute_point_features(closes, volumes)
    sentiment_scores = score_sentiment(returns, price_vs_ma, vol_z)

    ml_ohlcv = await fetch_daily_ohlcv_for_prediction(symbol)
    ml_result = ml_prediction(ml_ohlcv)
    is_ml_backed = ml_result is not None
    if ml_result is not None:
        direction, global_conf = ml_result
    else:
        direction, global_conf = prediction_from_series(sentiment_scores)
    insights = build_insights(
        symbol, closes, sentiment_scores, direction, global_conf, is_ml_backed=is_ml_backed
    )

    points: list[MarketDataPoint] = []
    for close, vol, ts, sent in zip(
        closes, volumes, timestamps, sentiment_scores
    ):
        # Slightly vary per-point confidence around global confidence. Bounds are wide
        # enough to allow the ML path's honestly low confidence (typically 45-58%,
        # see signal_engine/README.md) through without an artificial floor, while still
        # capping the heuristic fallback's occasional wide swings.
        jitter = int(min(8, max(-8, (sent * 15))))
        confidence = int(min(75, max(35, global_conf + jitter)))

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

    buckets = sentiment_buckets(sentiment_scores)
    news = await fetch_finnhub_news(symbol)
    alerts = build_alerts_from_series(symbol, closes, volumes, sentiment_scores, news)
    keywords = build_keywords_from_news(news)

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
