"""Lightweight current price/change/volume lookups for summary cards."""
from __future__ import annotations

import httpx
import yfinance as yf

from core.config import FINNHUB_BASE_URL, FINNHUB_TOKEN
from schemas import QuoteItem


async def fetch_quote(symbol: str) -> QuoteItem | None:
    """
    Lightweight current price/change/volume for a "market at a glance" style
    summary card — distinct from fetch_daily_ohlcv_for_prediction, which
    requires 60+ bars for indicator warm-up and is overkill for a quick quote.

    Volume always comes from yfinance: Finnhub's free-tier /stock/candle
    endpoint returns 403 ("You don't have access to this resource") on this
    plan, confirmed directly — it's a plan restriction, not a bug. Finnhub's
    /quote endpoint (price/change/percent) is NOT restricted and is used when
    available since it's real-time rather than the last daily close; if that
    also fails, yfinance covers price/change/volume together in one call.
    """
    price: float | None = None
    change = 0.0
    change_pct = 0.0

    if FINNHUB_TOKEN:
        async with httpx.AsyncClient(base_url=FINNHUB_BASE_URL, timeout=10.0) as client:
            try:
                quote_resp = await client.get("/quote", params={"symbol": symbol, "token": FINNHUB_TOKEN})
                quote_resp.raise_for_status()
                quote = quote_resp.json()
                if quote.get("c"):
                    price = float(quote["c"])
                    change = float(quote.get("d") or 0.0)
                    change_pct = float(quote.get("dp") or 0.0)
            except httpx.HTTPError:
                pass  # fall through to yfinance for everything

    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d")
    except Exception:  # noqa: BLE001 - any yfinance failure means "skip this symbol"
        hist = None

    if hist is None or hist.empty:
        return None if price is None else QuoteItem(symbol=symbol, price=round(price, 2), change=round(change, 2), changePercent=round(change_pct, 2), volume=0)

    volume = int(hist.iloc[-1]["Volume"])
    if price is not None:
        return QuoteItem(symbol=symbol, price=round(price, 2), change=round(change, 2), changePercent=round(change_pct, 2), volume=volume)

    if len(hist) < 2:
        return None
    last, prev = hist.iloc[-1], hist.iloc[-2]
    change = float(last["Close"] - prev["Close"])
    change_pct = float(change / prev["Close"] * 100) if prev["Close"] else 0.0
    return QuoteItem(
        symbol=symbol,
        price=round(float(last["Close"]), 2),
        change=round(change, 2),
        changePercent=round(change_pct, 2),
        volume=int(last["Volume"]),
    )
