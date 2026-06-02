"""
Pure-pandas technical indicators.

No TA-Lib / C dependencies — everything is computed with pandas/numpy so the
project installs cleanly anywhere. Each function takes an OHLCV DataFrame with
columns: open, high, low, close, volume (lower-case) and a DatetimeIndex.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# --- helpers ---------------------------------------------------------------

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    ranges = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


# --- momentum --------------------------------------------------------------

def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = _ema(df["close"], fast) - _ema(df["close"], slow)
    signal_line = _ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def stochastic(df: pd.DataFrame, k: int = 14, d: int = 3):
    low_k = df["low"].rolling(k).min()
    high_k = df["high"].rolling(k).max()
    percent_k = 100 * (df["close"] - low_k) / (high_k - low_k)
    percent_d = percent_k.rolling(d).mean()
    return percent_k, percent_d


def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma_tp) / (0.015 * mad)


def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"].rolling(period).max()
    low = df["low"].rolling(period).min()
    return -100 * (high - df["close"]) / (high - low)


def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    raw_money = tp * df["volume"]
    direction = np.sign(tp.diff().fillna(0))
    pos_flow = raw_money.where(direction > 0, 0.0).rolling(period).sum()
    neg_flow = raw_money.where(direction < 0, 0.0).rolling(period).sum()
    ratio = pos_flow / neg_flow.replace(0, np.nan)
    return 100 - (100 / (1 + ratio))


# --- trend -----------------------------------------------------------------

def ema_cross(df: pd.DataFrame, fast: int = 12, slow: int = 26):
    return _ema(df["close"], fast), _ema(df["close"], slow)


def sma_cross(df: pd.DataFrame, fast: int = 50, slow: int = 200):
    return _sma(df["close"], fast), _sma(df["close"], slow)


def adx(df: pd.DataFrame, period: int = 14):
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = _true_range(df)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_line = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx_line, plus_di, minus_di


def parabolic_sar(df: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    high, low = df["high"].values, df["low"].values
    sar = np.zeros(len(df))
    if len(df) == 0:
        return pd.Series(sar, index=df.index)
    bull = True
    af = step
    ep = high[0]
    sar[0] = low[0]
    for i in range(1, len(df)):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
        if bull:
            if low[i] < sar[i]:
                bull = False
                sar[i] = ep
                ep = low[i]
                af = step
            elif high[i] > ep:
                ep = high[i]
                af = min(af + step, max_step)
        else:
            if high[i] > sar[i]:
                bull = True
                sar[i] = ep
                ep = high[i]
                af = step
            elif low[i] < ep:
                ep = low[i]
                af = min(af + step, max_step)
    return pd.Series(sar, index=df.index)


def ichimoku(df: pd.DataFrame):
    high9 = df["high"].rolling(9).max()
    low9 = df["low"].rolling(9).min()
    tenkan = (high9 + low9) / 2
    high26 = df["high"].rolling(26).max()
    low26 = df["low"].rolling(26).min()
    kijun = (high26 + low26) / 2
    span_a = ((tenkan + kijun) / 2).shift(26)
    high52 = df["high"].rolling(52).max()
    low52 = df["low"].rolling(52).min()
    span_b = ((high52 + low52) / 2).shift(26)
    return tenkan, kijun, span_a, span_b


# --- volatility / bands ----------------------------------------------------

def bollinger(df: pd.DataFrame, period: int = 20, mult: float = 2.0):
    mid = _sma(df["close"], period)
    std = df["close"].rolling(period).std()
    upper = mid + mult * std
    lower = mid - mult * std
    return upper, mid, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return _true_range(df).ewm(alpha=1 / period, adjust=False).mean()


def donchian(df: pd.DataFrame, period: int = 20):
    upper = df["high"].rolling(period).max()
    lower = df["low"].rolling(period).min()
    return upper, lower


# --- volume ----------------------------------------------------------------

def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff().fillna(0))
    return (direction * df["volume"]).cumsum()


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()
