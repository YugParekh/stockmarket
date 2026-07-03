"""Real price/candle data fetching: Finnhub primary, yfinance fallback."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx
import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import HTTPException

from core.config import FINNHUB_BASE_URL, FINNHUB_TOKEN


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


async def fetch_finnhub_candles(symbol: str, cfg: RangeConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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


async def fetch_daily_ohlcv_for_prediction(symbol: str, lookback_days: int = 400) -> pd.DataFrame | None:
    """
    Fetches daily-resolution OHLCV for the ML prediction model, independent of the
    chart's selected `range`/resolution — the model was trained on daily bars (see
    signal_engine/README.md), so intraday candles (used for the 1D/5D chart views)
    would be statistically invalid inputs. Finnhub daily candles first, yfinance
    fallback, matching the data-source hierarchy used elsewhere in this module. Returns
    None if fewer than 60 bars are available (not enough for the model's longest
    warm-up window, SMA/EMA-50), so callers can fall back to the heuristic.
    """
    if FINNHUB_TOKEN:
        now_ts = int(datetime.utcnow().timestamp())
        from_ts = now_ts - lookback_days * 24 * 60 * 60
        params = {
            "symbol": symbol,
            "resolution": "D",
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
                    c = data.get("c", [])
                    if len(c) >= 60:
                        idx = pd.to_datetime(data.get("t", []), unit="s")
                        return pd.DataFrame(
                            {
                                "open": data.get("o", []),
                                "high": data.get("h", []),
                                "low": data.get("l", []),
                                "close": c,
                                "volume": data.get("v", []),
                            },
                            index=idx,
                        ).sort_index()
            except httpx.HTTPError:
                pass  # fall through to yfinance

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y", interval="1d")
    except Exception:  # noqa: BLE001 - any yfinance failure means "no ML prediction this time"
        return None

    if hist.empty or len(hist) < 60:
        return None

    hist = hist.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    )
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    return hist[["open", "high", "low", "close", "volume"]].sort_index()
