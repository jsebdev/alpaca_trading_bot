"""
Configuration management for trading bot.

Handles loading environment variables and providing configuration
parameters throughout the application.
"""

import os
from typing import List
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """
    Configuration container for trading bot.

    Attributes:
        alpaca_api_key: Alpaca API key
        alpaca_api_secret: Alpaca API secret
        paper_trading: Whether to use paper trading (default: True)
        watchlist: List of stock symbols to monitor
        cash_allocation_percent: Percentage of available cash to allocate per trade
        lookback_days: Number of days to look back for candle size calculation
    """

    alpaca_api_key: str
    alpaca_api_secret: str
    paper_trading: bool = True
    watchlist: List[str] = None
    cash_allocation_percent: float = 0.05
    lookback_days: int = 5

    @classmethod
    def from_env(cls, watchlist: List[str] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            watchlist: Optional list of stock symbols. If not provided,
                      defaults to AAPL, MSFT, GOOGL, AMZN, TSLA

        Returns:
            Config instance with loaded values

        Raises:
            ValueError: If required environment variables are missing
        """
        load_dotenv()

        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError(
                "ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env file"
            )

        default_watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        return cls(
            alpaca_api_key=api_key,
            alpaca_api_secret=api_secret,
            paper_trading=os.getenv("PAPER_TRADING", "true").lower() == "true",
            watchlist=watchlist or default_watchlist,
            cash_allocation_percent=float(
                os.getenv("CASH_ALLOCATION_PERCENT", "0.05")
            ),
            lookback_days=int(os.getenv("LOOKBACK_DAYS", "5")),
        )

    def validate(self) -> None:
        """
        Validate configuration parameters.

        Raises:
            ValueError: If any configuration parameter is invalid
        """
        if not 0 < self.cash_allocation_percent <= 1:
            raise ValueError(
                f"cash_allocation_percent must be between 0 and 1, "
                f"got {self.cash_allocation_percent}"
            )

        if self.lookback_days < 1:
            raise ValueError(
                f"lookback_days must be at least 1, got {self.lookback_days}"
            )

        if not self.watchlist:
            raise ValueError("watchlist cannot be empty")
