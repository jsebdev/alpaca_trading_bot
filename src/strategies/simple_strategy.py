import logging
from typing import Optional

from .base_strategy import BaseStrategy, TradeSignal
from utils.market_data import MarketDataFetcher


logger = logging.getLogger(__name__)


class SimpleGapDownStrategy(BaseStrategy):
    def __init__(
        self,
        cash_allocation_percent: float,
        lookback_days: int,
    ):
        self.cash_allocation_percent = cash_allocation_percent
        self.lookback_days = lookback_days

    def get_name(self) -> str:
        return "Simple Gap-Down Strategy"

    def get_description(self) -> str:
        return (
            f"Buys stocks gapping down (open < prev close) with "
            f"{self.cash_allocation_percent*100}% cash allocation. "
            f"TP/SL based on {self.lookback_days}-day average candle size."
        )

    def evaluate(
        self,
        symbol: str,
        available_cash: float,
        market_data_fetcher: MarketDataFetcher,
        **kwargs,
    ) -> TradeSignal:
        notional = available_cash * self.cash_allocation_percent
        logger.debug('>>>>> simple_strategy.py:83 "notional"')
        logger.debug(notional)

        # Minimum trade size check
        if notional < 1.0:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason=f"Insufficient cash (${available_cash})",
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
                reason=f"No gap down (open=${current_open} >= prev_close=${prev_close})",
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
                f"Gap down {gap_percent}% "
                f"(open=${current_open}, prev_close=${prev_close}), "
                f"avg_candle=${avg_candle_size}, "
                f"TP=${take_profit_price}, SL=${stop_loss_price}"
            ),
        )
