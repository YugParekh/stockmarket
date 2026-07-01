"""
Builds a labeled historical dataset (technical-indicator features + forward-direction
labels) per symbol from real yfinance daily OHLCV data, for backtesting and model training.

Label definition: for horizon h in {1, 5} trading days, label_h = 1 if close[t+h] > close[t]
else 0. This is a forward-looking label computed from data *after* time t — it must NEVER be
used as a feature, only as the target the walk-forward backtest evaluates predictions against.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf

from signal_engine.indicators import FEATURE_COLUMNS, build_features

HORIZONS = (1, 5)

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "SPY", "QQQ"]

DATA_CACHE_DIR = Path(__file__).parent / "data_cache"


@dataclass
class SymbolDataset:
    symbol: str
    frame: pd.DataFrame  # index: date, columns: FEATURE_COLUMNS + close + label_1 + label_5


def fetch_ohlcv(
    symbol: str,
    period: str = "8y",
    use_cache: bool = True,
    max_retries: int = 4,
    initial_backoff_s: float = 2.0,
) -> pd.DataFrame:
    """
    Downloads daily OHLCV from yfinance, with disk caching (parquet, keyed by symbol+period)
    so repeated backtest runs are reproducible and don't re-hit the network, plus retry-with-
    backoff since yfinance is prone to transient rate-limiting.
    """
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = DATA_CACHE_DIR / f"{symbol}_{period}.parquet"

    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d", auto_adjust=True)
            if hist.empty:
                raise ValueError(f"No data returned for {symbol}")
            hist = hist.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
            hist.index = pd.to_datetime(hist.index).tz_localize(None)
            hist.index.name = "date"
            result = hist[["open", "high", "low", "close", "volume"]].sort_index()

            if use_cache:
                result.to_parquet(cache_path)
            return result
        except Exception as exc:  # noqa: BLE001 - retry on any transient failure
            last_exc = exc
            if attempt < max_retries - 1:
                sleep_s = initial_backoff_s * (2**attempt)
                print(
                    f"[dataset] fetch failed for {symbol} (attempt {attempt + 1}/{max_retries}): "
                    f"{exc!r}; retrying in {sleep_s:.1f}s"
                )
                time.sleep(sleep_s)

    raise RuntimeError(f"Failed to fetch {symbol} after {max_retries} attempts") from last_exc


def build_symbol_dataset(symbol: str, period: str = "8y") -> SymbolDataset:
    ohlcv = fetch_ohlcv(symbol, period=period)
    features = build_features(ohlcv)

    frame = features.copy()
    frame["close"] = ohlcv["close"]

    for h in HORIZONS:
        forward_return = ohlcv["close"].shift(-h) / ohlcv["close"] - 1.0
        frame[f"label_{h}"] = (forward_return > 0).astype(float)
        frame[f"forward_return_{h}"] = forward_return

    # Drop warm-up rows (indicator NaNs) and trailing rows with no forward label.
    frame = frame.dropna(subset=FEATURE_COLUMNS + [f"label_{h}" for h in HORIZONS])

    return SymbolDataset(symbol=symbol, frame=frame)


def build_all_datasets(symbols: list[str] | None = None, period: str = "8y") -> dict[str, SymbolDataset]:
    symbols = symbols or DEFAULT_SYMBOLS
    datasets: dict[str, SymbolDataset] = {}
    for symbol in symbols:
        try:
            datasets[symbol] = build_symbol_dataset(symbol, period=period)
        except Exception as exc:  # noqa: BLE001 - log and continue with remaining symbols
            print(f"[dataset] skipping {symbol}: {exc}")
    return datasets
