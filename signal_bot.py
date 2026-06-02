"""
Signal / alert bot  (for MANUAL trading on Abyan or any app).

Computes the 16-strategy composite signal for each symbol and, when the score
crosses the threshold, sends you a Telegram alert describing what to do. It
places NO orders — you execute the trade yourself in Abyan. This keeps you
fully within Abyan's terms of service.

Run once (e.g. from cron):   python signal_bot.py
Run as a loop every N min:   python signal_bot.py --loop 15
"""

from __future__ import annotations

import argparse
import time

import requests

from config import CONFIG
from data_feed import fetch
from strategies import StrategyEngine


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{CONFIG.telegram_token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": CONFIG.telegram_chat_id, "text": text},
        timeout=15,
    )
    resp.raise_for_status()


def run_once(notify: bool = True) -> None:
    engine = StrategyEngine(threshold=CONFIG.signal_threshold)
    for symbol in CONFIG.symbols:
        try:
            df = fetch(symbol, CONFIG.timeframe)
            sig = engine.evaluate(symbol, df)
        except Exception as exc:
            print(f"[skip] {symbol}: {exc}")
            continue

        print(sig.summary())
        print("-" * 60)

        if sig.action in ("BUY", "SELL") and notify:
            # Suggest an ATR-based stop so the manual trade has risk control.
            if sig.action == "BUY":
                stop = sig.price - 1.5 * sig.atr
                target = sig.price + 3.0 * sig.atr
            else:
                stop = sig.price + 1.5 * sig.atr
                target = sig.price - 3.0 * sig.atr
            msg = (
                f"🔔 ABYAN MANUAL SIGNAL\n"
                f"{sig.symbol}: {sig.action}\n"
                f"price: {sig.price:.2f}\n"
                f"votes: {sig.buy_votes} buy / {sig.sell_votes} sell "
                f"(score {sig.score:+d})\n"
                f"suggested stop: {stop:.2f}\n"
                f"suggested target: {target:.2f}\n"
                f"⚠️ Execute manually in Abyan. Not financial advice."
            )
            try:
                send_telegram(msg)
                print(f"  -> alert sent for {symbol}")
            except Exception as exc:
                print(f"  -> telegram failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="16-strategy signal/alert bot")
    parser.add_argument("--loop", type=int, metavar="MIN",
                        help="repeat every MIN minutes instead of running once")
    parser.add_argument("--no-notify", action="store_true",
                        help="print signals only, do not send Telegram alerts")
    args = parser.parse_args()

    notify = not args.no_notify
    if notify:
        CONFIG.require_telegram()

    if args.loop:
        print(f"Looping every {args.loop} min. Ctrl-C to stop.")
        while True:
            run_once(notify=notify)
            time.sleep(args.loop * 60)
    else:
        run_once(notify=notify)


if __name__ == "__main__":
    main()
