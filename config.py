"""Central config loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


@dataclass
class Config:
    # Alpaca
    alpaca_key: str = _get("ALPACA_API_KEY")
    alpaca_secret: str = _get("ALPACA_API_SECRET")
    alpaca_base_url: str = _get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    # Telegram
    telegram_token: str = _get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = _get("TELEGRAM_CHAT_ID")

    # Strategy
    symbols: tuple = tuple(
        s.strip() for s in _get("SYMBOLS", "AAPL,MSFT,SPY").split(",") if s.strip()
    )
    timeframe: str = _get("TIMEFRAME", "1d")
    signal_threshold: int = int(_get("SIGNAL_THRESHOLD", "6") or 6)
    max_position_pct: float = float(_get("MAX_POSITION_PCT", "5") or 5)

    @property
    def is_paper(self) -> bool:
        return "paper" in self.alpaca_base_url

    def require_alpaca(self) -> None:
        if not self.alpaca_key or not self.alpaca_secret:
            raise SystemExit(
                "Missing ALPACA_API_KEY / ALPACA_API_SECRET. "
                "Copy .env.example to .env and fill them in."
            )

    def require_telegram(self) -> None:
        if not self.telegram_token or not self.telegram_chat_id:
            raise SystemExit(
                "Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID. "
                "See .env.example for how to obtain them."
            )


CONFIG = Config()
