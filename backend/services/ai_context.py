"""Builds the grounded context block ai_insights.py's prompts are built from,
reusing the same real data the dashboard already computes."""
from __future__ import annotations

import ai_insights
from services.market_data import fetch_daily_ohlcv_for_prediction
from services.news import fetch_finnhub_news
from services.prediction import ml_prediction
from services.sentiment import label_from_score


async def build_ai_context(symbol: str) -> str:
    ml_ohlcv = await fetch_daily_ohlcv_for_prediction(symbol)
    ml_result = ml_prediction(ml_ohlcv)

    if ml_result is not None:
        direction, confidence = ml_result
        is_ml_backed = True
        latest_price = float(ml_ohlcv["close"].iloc[-1])
    else:
        direction, confidence, is_ml_backed = "UP", 50, False
        latest_price = 0.0

    news = await fetch_finnhub_news(symbol)
    headlines = [n.headline for n in news[:5]]
    if news:
        pos = sum(1 for n in news if n.sentiment == "Positive")
        neg = sum(1 for n in news if n.sentiment == "Negative")
        avg_sent = (pos - neg) / len(news)
    else:
        avg_sent = 0.0
    sentiment_label = label_from_score(avg_sent)

    if ml_ohlcv is not None and len(ml_ohlcv) > 10:
        returns = ml_ohlcv["close"].pct_change().dropna()
        vol = float(returns.tail(10).std())
        value_at_risk_pct = round(1.65 * vol * 100.0, 2)
        volatility_score = min(100.0, vol * 1000.0)
        risk_level = "Low" if volatility_score < 25 else ("Medium" if volatility_score < 55 else "High")
    else:
        value_at_risk_pct = 0.0
        risk_level = "Medium"

    return ai_insights.build_context_block(
        symbol=symbol,
        latest_price=latest_price,
        direction=direction,
        confidence=confidence,
        is_ml_backed=is_ml_backed,
        risk_level=risk_level,
        value_at_risk_pct=value_at_risk_pct,
        sentiment_label=sentiment_label,
        news_headlines=headlines,
    )
