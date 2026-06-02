"""
Market-data feed.

Uses yfinance so the signal/alert bot works for ANY market (US tickers, or
Saudi Tadawul symbols like 2222.SR for Aramco — handy for picking what to
trade manually in Abyan). Returns a normalised lower-case OHLCV DataFrame.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf

# Map our timeframe strings to (yfinance interval, lookback period).
_TF = {
    "1d": ("1d", "2y"),
    "1h": ("1h", "60d"),
    "30m": ("30m", "30d"),
    "15m": ("15m", "30d"),
    "5m": ("5m", "7d"),
}


def fetch(symbol: str, timeframe: str = "1d") -> pd.DataFrame:
    interval, period = _TF.get(timeframe, ("1d", "2y"))
    raw = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if raw.empty:
        raise ValueError(f"No data returned for {symbol} ({timeframe})")

    # yfinance may return a MultiIndex column frame for single tickers.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    return df.dropna()
