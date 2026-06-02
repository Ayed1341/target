"""Strategy package: indicators + the 16-strategy signal engine."""

from .engine import StrategyEngine, StrategyResult, CompositeSignal

__all__ = ["StrategyEngine", "StrategyResult", "CompositeSignal"]
