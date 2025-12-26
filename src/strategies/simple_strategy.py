"""
Simple gap-down trading strategy.

This strategy:
1. Only buys stocks that gap down (open < previous close)
2. Allocates a fixed percentage of available cash per trade
3. Sets take profit and stop loss based on average candle size
"""

import logging
from typing import Optional

from .base_strategy import BaseStrategy, TradeSignal
from utils.market_data import MarketDataFetcher


class SimpleGapDownStrategy(BaseStrategy):
    """
    Strategy that buys stocks gapping down with bracket orders.

    Entry Criteria:
    - Current open price < previous day's close price (gap down)

    Position Sizing:
    - Uses a fixed percentage of available cash per trade

    Risk Management:
    - Take profit = entry price + average candle size (last N days)
    - Stop loss = entry price - average candle size (last N days)
    """

    def __init__(
        self,
        cash_allocation_percent: float,
        lookback_days: int,
        logger: logging.Logger,
    ):
        """
        Initialize the gap-down strategy.

        Args:
            cash_allocation_percent: Percentage of available cash to allocate (0-1)
            lookback_days: Number of days for average candle size calculation
            logger: Logger instance
        """
        super().__init__(logger)
        self.cash_allocation_percent = cash_allocation_percent
        self.lookback_days = lookback_days

    def get_name(self) -> str:
        """Get strategy name."""
        return "Simple Gap-Down Strategy"

    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"Buys stocks gapping down (open < prev close) with "
            f"{self.cash_allocation_percent*100:.1f}% cash allocation. "
            f"TP/SL based on {self.lookback_days}-day average candle size."
        )

    def evaluate(
        self,
        symbol: str,
        available_cash: float,
        market_data_fetcher: MarketDataFetcher,
        **kwargs,
    ) -> TradeSignal:
        """
        Evaluate whether to buy a symbol based on gap-down criteria.

        Args:
            symbol: Stock symbol to evaluate
            available_cash: Current available cash
            market_data_fetcher: Market data fetcher instance
            **kwargs: Additional parameters (unused)

        Returns:
            TradeSignal with trade decision and parameters
        """
        # Calculate notional amount to invest
        notional = available_cash * self.cash_allocation_percent

        # Minimum trade size check
        if notional < 1.0:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason=f"Insufficient cash (${available_cash:.2f})",
            )

        # Get gap information
        gap_info = market_data_fetcher.get_gap_info(symbol)

        if gap_info is None:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason="Insufficient historical data",
            )

        prev_close, current_open, gap_percent = gap_info

        # Check for gap down: current open < previous close
        if current_open >= prev_close:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason=f"No gap down (open=${current_open:.2f} >= prev_close=${prev_close:.2f})",
            )

        # Calculate average candle size for TP/SL
        avg_candle_size = market_data_fetcher.calculate_average_candle_size(
            symbol, self.lookback_days
        )

        if avg_candle_size is None:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason="Cannot calculate average candle size",
            )

        # Calculate bracket order prices
        entry_price = current_open
        take_profit_price = entry_price + avg_candle_size
        stop_loss_price = entry_price - avg_candle_size

        # Ensure stop loss is not negative
        if stop_loss_price <= 0:
            stop_loss_price = entry_price * 0.5  # Fallback to 50% stop

        return TradeSignal(
            symbol=symbol,
            should_trade=True,
            notional=notional,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            reason=(
                f"Gap down {gap_percent:.2f}% "
                f"(open=${current_open:.2f}, prev_close=${prev_close:.2f}), "
                f"avg_candle=${avg_candle_size:.2f}, "
                f"TP=${take_profit_price:.2f}, SL=${stop_loss_price:.2f}"
            ),
        )
