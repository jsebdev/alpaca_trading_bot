"""
Example: How to create and use custom trading strategies.

This demonstrates the strategy injection pattern, showing how easy it is
to create new strategies and swap them in the bot.
"""

import logging
from strategies import BaseStrategy, TradeSignal
from utils.market_data import MarketDataFetcher
from bots.day_bot import main
from utils import setup_logger


class MomentumStrategy(BaseStrategy):
    """
    Example custom strategy: Buy stocks with strong upward momentum.

    This strategy demonstrates how to create your own trading logic
    by inheriting from BaseStrategy.
    """

    def __init__(self, lookback_days: int, min_gain_percent: float, logger: logging.Logger):
        """
        Initialize momentum strategy.

        Args:
            lookback_days: Number of days to check for momentum
            min_gain_percent: Minimum percentage gain required
            logger: Logger instance
        """
        super().__init__(logger)
        self.lookback_days = lookback_days
        self.min_gain_percent = min_gain_percent

    def get_name(self) -> str:
        return "Momentum Strategy"

    def get_description(self) -> str:
        return (
            f"Buys stocks with >{self.min_gain_percent}% gain "
            f"over last {self.lookback_days} days"
        )

    def evaluate(
        self,
        symbol: str,
        available_cash: float,
        market_data_fetcher: MarketDataFetcher,
        **kwargs,
    ) -> TradeSignal:
        """Evaluate based on momentum criteria."""

        # Get historical data
        bars = market_data_fetcher.get_historical_bars(symbol, self.lookback_days + 1)

        if len(bars) < self.lookback_days + 1:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason="Insufficient data",
            )

        # Calculate momentum
        old_price = bars[0].close
        current_price = bars[-1].close
        gain_percent = ((current_price - old_price) / old_price) * 100

        # Check if meets momentum threshold
        if gain_percent < self.min_gain_percent:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason=f"Momentum {gain_percent:.2f}% < {self.min_gain_percent}%",
            )

        # Calculate position size (5% of available cash)
        notional = available_cash * 0.05

        if notional < 1.0:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason="Insufficient cash",
            )

        # Simple take profit and stop loss (5% each)
        take_profit = current_price * 1.05
        stop_loss = current_price * 0.95

        return TradeSignal(
            symbol=symbol,
            should_trade=True,
            notional=notional,
            take_profit_price=take_profit,
            stop_loss_price=stop_loss,
            reason=f"Strong momentum: {gain_percent:.2f}% over {self.lookback_days} days",
        )


class ConservativeStrategy(BaseStrategy):
    """
    Example: Conservative strategy that only trades blue-chip stocks
    with low volatility.
    """

    def __init__(self, max_volatility: float, logger: logging.Logger):
        super().__init__(logger)
        self.max_volatility = max_volatility

    def get_name(self) -> str:
        return "Conservative Low-Volatility Strategy"

    def get_description(self) -> str:
        return f"Only trades stocks with volatility < {self.max_volatility}"

    def evaluate(
        self,
        symbol: str,
        available_cash: float,
        market_data_fetcher: MarketDataFetcher,
        **kwargs,
    ) -> TradeSignal:
        """Evaluate based on volatility."""

        # Get 20 days of data to calculate volatility
        bars = market_data_fetcher.get_historical_bars(symbol, 20)

        if len(bars) < 20:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason="Insufficient data for volatility calculation",
            )

        # Calculate simple volatility (average of daily ranges)
        daily_ranges = [
            ((bar.high - bar.low) / bar.close) * 100
            for bar in bars
        ]
        avg_volatility = sum(daily_ranges) / len(daily_ranges)

        if avg_volatility > self.max_volatility:
            return TradeSignal(
                symbol=symbol,
                should_trade=False,
                reason=f"Too volatile: {avg_volatility:.2f}% > {self.max_volatility}%",
            )

        # Conservative position sizing: only 3% of cash
        notional = available_cash * 0.03
        current_price = bars[-1].close

        return TradeSignal(
            symbol=symbol,
            should_trade=True,
            notional=notional,
            take_profit_price=current_price * 1.03,  # 3% gain target
            stop_loss_price=current_price * 0.98,    # 2% stop loss
            reason=f"Low volatility: {avg_volatility:.2f}%",
        )


if __name__ == "__main__":
    """
    Example usage: Run the bot with different strategies.

    To use a custom strategy in day_bot.py, modify the main() function
    to instantiate your strategy instead of SimpleGapDownStrategy.
    """

    print("Example custom strategies created!")
    print("\nTo use a custom strategy:")
    print("1. Create your strategy class inheriting from BaseStrategy")
    print("2. Implement evaluate(), get_name(), and get_description()")
    print("3. In bots/day_bot.py, replace SimpleGapDownStrategy with your strategy")
    print("\nExample strategies in this file:")
    print("- MomentumStrategy: Buys stocks with strong upward momentum")
    print("- ConservativeStrategy: Only trades low-volatility stocks")
