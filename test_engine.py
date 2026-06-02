"""Smoke test: run all 16 strategies on synthetic data, no network needed."""

import numpy as np
import pandas as pd

from strategies import StrategyEngine


def make_df(n=300, seed=1):
    rng = np.random.default_rng(seed)
    # Trending random walk so several strategies actually trigger.
    rets = rng.normal(0.0005, 0.02, n) + np.linspace(0, 0.002, n)
    close = 100 * np.exp(np.cumsum(rets))
    high = close * (1 + rng.uniform(0, 0.01, n))
    low = close * (1 - rng.uniform(0, 0.01, n))
    open_ = close * (1 + rng.uniform(-0.005, 0.005, n))
    vol = rng.integers(1_000_000, 5_000_000, n).astype(float)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=idx,
    )


def test_engine_runs_and_votes():
    engine = StrategyEngine(threshold=6)
    sig = engine.evaluate("TEST", make_df())
    assert len(sig.results) == 16, "all 16 strategies must report"
    assert sig.action in ("BUY", "SELL", "HOLD")
    assert sig.buy_votes + sig.sell_votes <= 16
    # No strategy should have errored out.
    errs = [r for r in sig.results if r.reason.startswith("error:")]
    assert not errs, f"strategies errored: {errs}"
    return sig


if __name__ == "__main__":
    sig = test_engine_runs_and_votes()
    print(sig.summary())
    print("\nOK: 16/16 strategies executed cleanly.")
