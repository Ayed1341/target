"""
The 16-strategy signal engine.

Each strategy inspects the latest bar(s) and votes:  +1 (buy), -1 (sell),
0 (neutral). A composite signal is produced by summing the votes and comparing
against a threshold. This same engine powers BOTH the Alpaca live trader and
the Abyan signal/alert bot — they only differ in what they do with the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

import pandas as pd

from . import indicators as ind


@dataclass
class StrategyResult:
    name: str
    vote: int           # -1, 0, +1
    reason: str         # human-readable explanation


@dataclass
class CompositeSignal:
    symbol: str
    action: str         # "BUY", "SELL", "HOLD"
    score: int          # sum of votes
    buy_votes: int
    sell_votes: int
    price: float
    atr: float          # latest ATR, useful for stop sizing
    results: List[StrategyResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"{self.symbol}: {self.action}  "
            f"(score {self.score:+d} | {self.buy_votes} buy / {self.sell_votes} sell)",
            f"  price={self.price:.2f}  atr={self.atr:.2f}",
        ]
        for r in self.results:
            arrow = {1: "▲ BUY ", -1: "▼ SELL", 0: "· ----"}[r.vote]
            lines.append(f"   {arrow} {r.name}: {r.reason}")
        return "\n".join(lines)


# A strategy is a function: (df) -> StrategyResult, reading the latest values.

def _last(s: pd.Series) -> float:
    return float(s.iloc[-1])


def _prev(s: pd.Series) -> float:
    return float(s.iloc[-2])


# --- the 16 strategies -----------------------------------------------------

def s_rsi(df):
    r = _last(ind.rsi(df))
    if r < 30:
        return StrategyResult("RSI", 1, f"oversold ({r:.0f}<30)")
    if r > 70:
        return StrategyResult("RSI", -1, f"overbought ({r:.0f}>70)")
    return StrategyResult("RSI", 0, f"neutral ({r:.0f})")


def s_macd(df):
    macd_line, signal_line, hist = ind.macd(df)
    if _prev(hist) <= 0 < _last(hist):
        return StrategyResult("MACD", 1, "bullish cross")
    if _prev(hist) >= 0 > _last(hist):
        return StrategyResult("MACD", -1, "bearish cross")
    return StrategyResult("MACD", 0, "no cross")


def s_stochastic(df):
    k, d = ind.stochastic(df)
    kv, dv = _last(k), _last(d)
    if kv < 20 and kv > dv:
        return StrategyResult("Stochastic", 1, f"oversold turn ({kv:.0f})")
    if kv > 80 and kv < dv:
        return StrategyResult("Stochastic", -1, f"overbought turn ({kv:.0f})")
    return StrategyResult("Stochastic", 0, f"neutral ({kv:.0f})")


def s_cci(df):
    c = _last(ind.cci(df))
    if c < -100:
        return StrategyResult("CCI", 1, f"oversold ({c:.0f})")
    if c > 100:
        return StrategyResult("CCI", -1, f"overbought ({c:.0f})")
    return StrategyResult("CCI", 0, f"neutral ({c:.0f})")


def s_williams(df):
    w = _last(ind.williams_r(df))
    if w < -80:
        return StrategyResult("Williams %R", 1, f"oversold ({w:.0f})")
    if w > -20:
        return StrategyResult("Williams %R", -1, f"overbought ({w:.0f})")
    return StrategyResult("Williams %R", 0, f"neutral ({w:.0f})")


def s_mfi(df):
    m = _last(ind.mfi(df))
    if m < 20:
        return StrategyResult("MFI", 1, f"oversold ({m:.0f})")
    if m > 80:
        return StrategyResult("MFI", -1, f"overbought ({m:.0f})")
    return StrategyResult("MFI", 0, f"neutral ({m:.0f})")


def s_ema_cross(df):
    fast, slow = ind.ema_cross(df)
    if _prev(fast) <= _prev(slow) and _last(fast) > _last(slow):
        return StrategyResult("EMA cross", 1, "fast crossed above slow")
    if _prev(fast) >= _prev(slow) and _last(fast) < _last(slow):
        return StrategyResult("EMA cross", -1, "fast crossed below slow")
    bias = 1 if _last(fast) > _last(slow) else -1
    return StrategyResult("EMA cross", 0, "trend " + ("up" if bias > 0 else "down"))


def s_sma_cross(df):
    fast, slow = ind.sma_cross(df)
    if pd.isna(_last(slow)):
        return StrategyResult("SMA 50/200", 0, "insufficient history")
    if _prev(fast) <= _prev(slow) and _last(fast) > _last(slow):
        return StrategyResult("SMA 50/200", 1, "golden cross")
    if _prev(fast) >= _prev(slow) and _last(fast) < _last(slow):
        return StrategyResult("SMA 50/200", -1, "death cross")
    return StrategyResult("SMA 50/200", 0, "no cross")


def s_adx(df):
    adx_line, plus_di, minus_di = ind.adx(df)
    a = _last(adx_line)
    if a < 20:
        return StrategyResult("ADX", 0, f"weak trend ({a:.0f})")
    if _last(plus_di) > _last(minus_di):
        return StrategyResult("ADX", 1, f"strong up-trend ({a:.0f})")
    return StrategyResult("ADX", -1, f"strong down-trend ({a:.0f})")


def s_psar(df):
    sar = ind.parabolic_sar(df)
    price = _last(df["close"])
    if price > _last(sar) and _prev(df["close"]) <= _prev(sar):
        return StrategyResult("Parabolic SAR", 1, "flip bullish")
    if price < _last(sar) and _prev(df["close"]) >= _prev(sar):
        return StrategyResult("Parabolic SAR", -1, "flip bearish")
    bias = 1 if price > _last(sar) else -1
    return StrategyResult("Parabolic SAR", 0, "bias " + ("up" if bias > 0 else "down"))


def s_ichimoku(df):
    tenkan, kijun, span_a, span_b = ind.ichimoku(df)
    price = _last(df["close"])
    if pd.isna(_last(span_a)) or pd.isna(_last(span_b)):
        return StrategyResult("Ichimoku", 0, "insufficient history")
    cloud_top = max(_last(span_a), _last(span_b))
    cloud_bot = min(_last(span_a), _last(span_b))
    if price > cloud_top:
        return StrategyResult("Ichimoku", 1, "above cloud")
    if price < cloud_bot:
        return StrategyResult("Ichimoku", -1, "below cloud")
    return StrategyResult("Ichimoku", 0, "inside cloud")


def s_bollinger(df):
    upper, mid, lower = ind.bollinger(df)
    price = _last(df["close"])
    if price < _last(lower):
        return StrategyResult("Bollinger", 1, "below lower band")
    if price > _last(upper):
        return StrategyResult("Bollinger", -1, "above upper band")
    return StrategyResult("Bollinger", 0, "within bands")


def s_donchian(df):
    upper, lower = ind.donchian(df)
    price = _last(df["close"])
    # Breakout of the prior channel (use shifted band so today's bar excluded).
    if price >= _prev(upper):
        return StrategyResult("Donchian", 1, "20-bar breakout up")
    if price <= _prev(lower):
        return StrategyResult("Donchian", -1, "20-bar breakout down")
    return StrategyResult("Donchian", 0, "inside channel")


def s_obv(df):
    o = ind.obv(df)
    slope = _last(o) - float(o.iloc[-5]) if len(o) >= 5 else 0.0
    if slope > 0:
        return StrategyResult("OBV", 1, "accumulation")
    if slope < 0:
        return StrategyResult("OBV", -1, "distribution")
    return StrategyResult("OBV", 0, "flat")


def s_vwap(df):
    v = _last(ind.vwap(df))
    price = _last(df["close"])
    if price > v:
        return StrategyResult("VWAP", 1, "above VWAP")
    if price < v:
        return StrategyResult("VWAP", -1, "below VWAP")
    return StrategyResult("VWAP", 0, "at VWAP")


def s_atr_breakout(df):
    a = ind.atr(df)
    price = _last(df["close"])
    prev = _prev(df["close"])
    move = price - prev
    if move > _last(a):
        return StrategyResult("ATR breakout", 1, "up-move > 1 ATR")
    if move < -_last(a):
        return StrategyResult("ATR breakout", -1, "down-move > 1 ATR")
    return StrategyResult("ATR breakout", 0, "within 1 ATR")


STRATEGIES: List[Callable[[pd.DataFrame], StrategyResult]] = [
    s_rsi, s_macd, s_stochastic, s_cci, s_williams, s_mfi,
    s_ema_cross, s_sma_cross, s_adx, s_psar, s_ichimoku,
    s_bollinger, s_donchian, s_obv, s_vwap, s_atr_breakout,
]
assert len(STRATEGIES) == 16, "expected exactly 16 strategies"


class StrategyEngine:
    """Runs all 16 strategies and aggregates them into one CompositeSignal."""

    def __init__(self, threshold: int = 6):
        # `threshold` = net score (buy_votes - sell_votes) needed to act.
        self.threshold = threshold

    def evaluate(self, symbol: str, df: pd.DataFrame) -> CompositeSignal:
        df = df.dropna().copy()
        if len(df) < 60:
            raise ValueError(
                f"{symbol}: need >=60 bars for reliable signals, got {len(df)}")

        results: List[StrategyResult] = []
        for strat in STRATEGIES:
            try:
                results.append(strat(df))
            except Exception as exc:  # never let one indicator kill the run
                results.append(StrategyResult(strat.__name__, 0, f"error: {exc}"))

        buy_votes = sum(1 for r in results if r.vote > 0)
        sell_votes = sum(1 for r in results if r.vote < 0)
        score = buy_votes - sell_votes

        action = "HOLD"
        if score >= self.threshold:
            action = "BUY"
        elif score <= -self.threshold:
            action = "SELL"

        return CompositeSignal(
            symbol=symbol,
            action=action,
            score=score,
            buy_votes=buy_votes,
            sell_votes=sell_votes,
            price=float(df["close"].iloc[-1]),
            atr=float(ind.atr(df).iloc[-1]),
            results=results,
        )
