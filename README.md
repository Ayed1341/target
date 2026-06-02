# 16-Strategy Trading Toolkit

Two ways to use one shared signal engine:

1. **`alpaca_trader.py`** — live algo-trading on **Alpaca** (paper money by
   default), a broker that explicitly allows automated trading.
2. **`signal_bot.py`** — a **signal/alert bot** that computes the same signals
   and sends you a **Telegram** alert so you can place the trade **manually in
   Abyan** (or any app). It never touches your Abyan account, so it stays
   within Abyan's terms of service.

> ⚠️ **About Abyan:** Abyan Capital has no public trading API, and automating
> its private app would violate its terms and risk your account. That's why
> Abyan is supported only through *manual* alerts, not direct trading.

## The 16 strategies

| # | Strategy | Type |
|---|----------|------|
| 1 | RSI (oversold/overbought) | momentum |
| 2 | MACD cross | momentum |
| 3 | Stochastic | momentum |
| 4 | CCI | momentum |
| 5 | Williams %R | momentum |
| 6 | MFI (volume momentum) | momentum |
| 7 | EMA 12/26 cross | trend |
| 8 | SMA 50/200 (golden/death) | trend |
| 9 | ADX (+DI/−DI) | trend |
| 10 | Parabolic SAR flip | trend |
| 11 | Ichimoku cloud | trend |
| 12 | Bollinger Bands | volatility |
| 13 | Donchian breakout | volatility |
| 14 | OBV | volume |
| 15 | VWAP | volume |
| 16 | ATR breakout | volatility |

Each strategy votes BUY (+1) / SELL (−1) / neutral (0). The engine sums the
votes; if the net score reaches `SIGNAL_THRESHOLD` it emits BUY/SELL,
otherwise HOLD.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in your keys
```

- **Alpaca keys:** sign up free at https://alpaca.markets and use the
  **Paper Trading** keys to start.
- **Telegram:** create a bot via @BotFather, then get your chat id from
  `https://api.telegram.org/bot<TOKEN>/getUpdates`.

## Usage

```bash
# See signals with no keys, no orders, no alerts:
python alpaca_trader.py --dry-run
python signal_bot.py --no-notify

# Manual-trading alerts to Telegram (for Abyan):
python signal_bot.py
python signal_bot.py --loop 15        # every 15 minutes

# Paper trading on Alpaca (fake money, real API):
python alpaca_trader.py
python alpaca_trader.py --loop 15
```

## Going live (real money)

The Alpaca trader defaults to the **paper** endpoint. Only after you've proven
the strategy on paper, change `ALPACA_BASE_URL` in `.env` to
`https://api.alpaca.markets`. **You are responsible for all real-money
trades.** Use position sizing (`MAX_POSITION_PCT`) and the suggested ATR stops.

## Disclaimer

This is educational software, **not financial advice**. Algorithmic trading can
lose money rapidly. Test on paper, start small, and never risk money you can't
afford to lose.
