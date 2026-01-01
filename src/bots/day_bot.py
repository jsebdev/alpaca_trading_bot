"""
Day trading bot.

Main orchestration script that:
1. Loads configuration
2. Initializes clients and utilities
3. Injects a trading strategy
4. Evaluates watchlist symbols
5. Places trades based on strategy signals
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    Config,
    AlpacaClientWrapper,
    MarketDataFetcher,
    OrderManager,
)
from utils.order_manager import BracketOrderParams
from strategies import BaseStrategy, SimpleGapDownStrategy, TradeSignal

logger = logging.getLogger(__name__)

class DayTradingBot:
    def __init__(
        self,
        config: Config,
        strategy: BaseStrategy,
        dry_run: bool = False,
    ):
        """
        Initialize the day trading bot.

        Args:
            config: Configuration object
            strategy: Trading strategy to use
            dry_run: If True, simulate trades without placing real orders
        """
        self.config = config
        self.strategy = strategy
        self.dry_run = dry_run

        # Initialize Alpaca clients and utilities
        self.alpaca_client = AlpacaClientWrapper(config)
        self.market_data_fetcher = MarketDataFetcher(
            self.alpaca_client.data_client
        )
        self.order_manager = OrderManager(
            self.alpaca_client.trading_client
        )

        logger.info(f"Initialized DayTradingBot with {strategy.get_name()}")
        logger.info(f"Strategy: {strategy.get_description()}")
        logger.info(f"Watchlist: {', '.join(config.watchlist)}")
        logger.info(f"Dry run mode: {dry_run}")

    def run(self) -> List[TradeSignal]:
        """
        Execute the trading bot workflow.

        Steps:
        1. Check account status and get available cash
        2. Evaluate all watchlist symbols using the strategy
        3. Place trades for symbols with positive signals

        Returns:
            List of trade signals generated

        Raises:
            Exception: If critical errors occur during execution
        """
        logger.info("=" * 60)
        logger.info(f"Starting bot run at {datetime.now()}")
        logger.info("=" * 60)

        try:
            if not self.alpaca_client.is_tradeable():
                logger.error("Account is not tradeable. Exiting.")
                return []

            account_summary = self.alpaca_client.get_account_summary()
            available_cash = account_summary["buying_power"]

            if available_cash <= 0:
                logger.warning("No buying power available. Exiting.")
                return []

            logger.info(f"Available buying power: ${available_cash:,.2f}")

            # Step 2: Evaluate watchlist using strategy
            logger.info(f"Evaluating {len(self.config.watchlist)} symbols...")

            signals = self.strategy.evaluate_watchlist(
                symbols=self.config.watchlist,
                available_cash=available_cash,
                market_data_fetcher=self.market_data_fetcher,
            )

            # Step 3: Place trades for positive signals
            trade_signals = [s for s in signals if s.should_trade]

            if not trade_signals:
                logger.info("No trade signals generated. Exiting.")
                return signals

            logger.info(f"Generated {len(trade_signals)} trade signals")

            for signal in trade_signals:
                self._execute_trade(signal)

            # Summary
            logger.info("=" * 60)
            logger.info("Bot run completed")
            logger.info(
                f"Signals: {len(trade_signals)} trades, "
                f"{len(signals) - len(trade_signals)} skips"
            )
            logger.info("=" * 60)

            return signals

        except Exception as e:
            logger.error(f"Critical error during bot run: {e}", exc_info=True)
            raise

    def _execute_trade(self, signal: TradeSignal) -> None:
        """
        Execute a single trade based on a signal.

        Args:
            signal: TradeSignal to execute
        """
        try:
            # If strategy provided bracket prices, use bracket order
            if signal.take_profit_price and signal.stop_loss_price:
                params = BracketOrderParams(
                    symbol=signal.symbol,
                    notional=signal.notional,
                    take_profit_price=signal.take_profit_price,
                    stop_loss_price=signal.stop_loss_price,
                )

                self.order_manager.place_bracket_order(params, dry_run=self.dry_run)

            # Otherwise use simple market order
            else:
                self.order_manager.place_market_order(
                    symbol=signal.symbol,
                    notional=signal.notional,
                    dry_run=self.dry_run,
                )

        except Exception as e:
            logger.error(
                f"Failed to execute trade for {signal.symbol}: {e}",
                exc_info=True,
            )


def main(dry_run: bool = False, watchlist: Optional[List[str]] = None):
    """
    Main entry point for the day trading bot.

    Args:
        dry_run: If True, simulate trades without placing real orders
        watchlist: Optional custom watchlist. If None, uses default from config.
    """

    try:
        # Load configuration
        config = Config.from_env(watchlist=watchlist)
        config.validate()

        # Initialize strategy
        strategy = SimpleGapDownStrategy(
            cash_allocation_percent=config.cash_allocation_percent,
            lookback_days=config.lookback_days,
        )

        # Initialize and run bot
        bot = DayTradingBot(
            config=config,
            strategy=strategy,
            dry_run=dry_run,
        )

        signals = bot.run()

        return signals

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Day trading bot")
    parser.add_argument(
        "--dry-run",
        action="store_false",
        help="Simulate trades without placing real orders",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Custom watchlist symbols (e.g., --symbols AAPL MSFT TSLA)",
    )

    args = parser.parse_args()

    main(dry_run=args.dry_run, watchlist=args.symbols)
