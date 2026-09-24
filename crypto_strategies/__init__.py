"""Research-oriented trading strategies for liquid crypto markets."""

from .engine import Bar, Signal, StrategyResult, backtest
from .strategies import BreakoutStrategy, TrendStrategy

__all__ = [
    "Bar",
    "Signal",
    "StrategyResult",
    "backtest",
    "BreakoutStrategy",
    "TrendStrategy",
]
