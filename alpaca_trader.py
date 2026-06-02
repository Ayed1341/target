"""
Live algo-trader on Alpaca (PAPER by default).

Evaluates the 16-strategy composite signal for each symbol and submits orders
through Alpaca's official API — a broker that explicitly permits automated
trading. Defaults to the paper-trading endpoint so you can prove the strategy
out with fake money before risking anything real.

  Dry run (no orders, just print):   python alpaca_trader.py --dry-run
  Paper trading (real API, fake $):  python alpaca_trader.py
  Loop every 15 min:                 python alpaca_trader.py --loop 15

Going live (real money) requires editing ALPACA_BASE_URL in .env to the live
endpoint. Do that ONLY after you trust the strategy. You are responsible for
any real-money trades.
"""

from __future__ import annotations

import argparse
import time

from config import CONFIG
from data_feed import fetch
from strategies import StrategyEngine, CompositeSignal


def _client():
    from alpaca.trading.client import TradingClient
    return TradingClient(
        CONFIG.alpaca_key,
        CONFIG.alpaca_secret,
        paper=CONFIG.is_paper,
    )


def _position_qty(client, symbol: str) -> float:
    try:
        return float(client.get_open_position(symbol).qty)
    except Exception:
        return 0.0


def _submit(client, symbol: str, side: str, qty: float) -> None:
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    client.submit_order(order)


def _act_on(client, sig: CompositeSignal, dry_run: bool) -> None:
    held = _position_qty(client, sig.symbol)

    if sig.action == "BUY" and held <= 0:
        account = client.get_account()
        budget = float(account.buying_power) * (CONFIG.max_position_pct / 100)
        qty = max(int(budget // sig.price), 0)
        if qty < 1:
            print(f"  {sig.symbol}: budget too small for 1 share, skipping")
            return
        print(f"  {sig.symbol}: BUY {qty} @ ~{sig.price:.2f}"
              f"{'  [dry-run]' if dry_run else ''}")
        if not dry_run:
            _submit(client, sig.symbol, "BUY", qty)

    elif sig.action == "SELL" and held > 0:
        print(f"  {sig.symbol}: SELL {held} (close position)"
              f"{'  [dry-run]' if dry_run else ''}")
        if not dry_run:
            _submit(client, sig.symbol, "SELL", held)

    else:
        print(f"  {sig.symbol}: no action (signal={sig.action}, held={held})")


def run_once(dry_run: bool) -> None:
    engine = StrategyEngine(threshold=CONFIG.signal_threshold)
    client = None if dry_run else _client()
    if dry_run:
        print("DRY RUN — no broker connection, no orders.\n")

    for symbol in CONFIG.symbols:
        try:
            df = fetch(symbol, CONFIG.timeframe)
            sig = engine.evaluate(symbol, df)
        except Exception as exc:
            print(f"[skip] {symbol}: {exc}")
            continue

        print(sig.summary())
        if not dry_run:
            _act_on(client, sig, dry_run=False)
        else:
            # In dry-run we still want to see the intended action.
            class _Fake:
                def get_open_position(self, *_): raise Exception("none")
                def get_account(self):
                    class A:  # noqa
                        buying_power = "100000"
                    return A()
            _act_on(_Fake(), sig, dry_run=True)
        print("-" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="16-strategy Alpaca trader")
    parser.add_argument("--dry-run", action="store_true",
                        help="evaluate + print intended orders, place none")
    parser.add_argument("--loop", type=int, metavar="MIN",
                        help="repeat every MIN minutes")
    args = parser.parse_args()

    if not args.dry_run:
        CONFIG.require_alpaca()
        mode = "PAPER" if CONFIG.is_paper else "*** LIVE (REAL MONEY) ***"
        print(f"Alpaca mode: {mode}")

    if args.loop:
        print(f"Looping every {args.loop} min. Ctrl-C to stop.")
        while True:
            run_once(dry_run=args.dry_run)
            time.sleep(args.loop * 60)
    else:
        run_once(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
