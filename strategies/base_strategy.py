"""
Base strategy abstract class.

Defines the interface that all trading strategies must implement,
enabling easy strategy swapping in the bot.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import logging


@dataclass
class TradeSignal:
    """
    Signal indicating whether to trade a symbol and with what parameters.

    Attributes:
        symbol: Stock symbol
        should_trade: Whether to execute a trade
        notional: Dollar amount to invest (if should_trade is True)
        take_profit_price: Optional take profit price
        stop_loss_price: Optional stop loss price
        reason: Human-readable reason for the decision
    """

    symbol: str
    should_trade: bool
    notional: float = 0.0
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    reason: str = ""


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All strategies must implement the evaluate() method which determines
    whether to trade a given symbol.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize the strategy.

        Args:
            logger: Logger instance for output
        """
        self.logger = logger

    @abstractmethod
    def evaluate(
        self,
        symbol: str,
        available_cash: float,
        market_data_fetcher: "MarketDataFetcher",
        **kwargs,
    ) -> TradeSignal:
        """
        Evaluate whether to trade a symbol.

        This method must be implemented by all strategy subclasses.

        Args:
            symbol: Stock symbol to evaluate
            available_cash: Current available cash for trading
            market_data_fetcher: MarketDataFetcher instance for data retrieval
            **kwargs: Additional strategy-specific parameters

        Returns:
            TradeSignal indicating whether and how to trade
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the strategy name.

        Returns:
            Human-readable strategy name
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get the strategy description.

        Returns:
            Detailed description of the strategy logic
        """
        pass

    def evaluate_watchlist(
        self,
        symbols: List[str],
        available_cash: float,
        market_data_fetcher: "MarketDataFetcher",
        **kwargs,
    ) -> List[TradeSignal]:
        """
        Evaluate all symbols in a watchlist.

        Args:
            symbols: List of stock symbols to evaluate
            available_cash: Current available cash for trading
            market_data_fetcher: MarketDataFetcher instance
            **kwargs: Additional strategy-specific parameters

        Returns:
            List of TradeSignals, one per symbol
        """
        signals = []
        remaining_cash = available_cash

        for symbol in symbols:
            self.logger.info(f"Evaluating {symbol} (cash: ${remaining_cash:.2f})")

            try:
                signal = self.evaluate(
                    symbol=symbol,
                    available_cash=remaining_cash,
                    market_data_fetcher=market_data_fetcher,
                    **kwargs,
                )

                signals.append(signal)

                # Update remaining cash if trade signal is positive
                if signal.should_trade:
                    remaining_cash -= signal.notional
                    self.logger.info(
                        f"{symbol}: TRADE - {signal.reason} "
                        f"(allocating ${signal.notional:.2f})"
                    )
                else:
                    self.logger.info(f"{symbol}: SKIP - {signal.reason}")

            except Exception as e:
                self.logger.error(
                    f"Error evaluating {symbol}: {e}",
                    exc_info=True,
                )
                signals.append(
                    TradeSignal(
                        symbol=symbol,
                        should_trade=False,
                        reason=f"Error: {str(e)}",
                    )
                )

        return signals
