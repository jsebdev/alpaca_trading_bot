"""
Trading strategies package.

This package contains trading strategy implementations that can be
injected into the trading bot.
"""

from .base_strategy import BaseStrategy, TradeSignal
from .simple_strategy import SimpleGapDownStrategy

__all__ = [
    "BaseStrategy",
    "TradeSignal",
    "SimpleGapDownStrategy",
]
