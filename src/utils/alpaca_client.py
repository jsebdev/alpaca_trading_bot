"""
Alpaca API client wrapper.

Provides a clean interface to Alpaca's trading and data APIs with
error handling and logging.
"""

import logging
from typing import Dict, Any
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.models import TradeAccount
from alpaca.common.exceptions import APIError

from .config import Config


logger = logging.getLogger(__name__)


class AlpacaClientWrapper:
    """
    Wrapper around Alpaca's trading and data clients.

    Provides centralized client management with error handling and logging.
    """

    # def __init__(self, config: Config, logger: logging.Logger):
    def __init__(self, config: Config):
        """
        Initialize Alpaca clients.

        Args:
            config: Configuration object with API credentials
            logger: Logger instance for output
        """
        self.config = config
        # self.logger = logger

        self.trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_api_secret,
            paper=config.paper_trading,
        )

        self.data_client = StockHistoricalDataClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_api_secret,
        )

        logger.info(
            f"Initialized Alpaca clients (paper_trading={config.paper_trading})"
        )

    def get_account(self) -> TradeAccount:
        """
        Get account information.

        Returns:
            TradeAccount object with current account details

        Raises:
            APIError: If the API request fails
        """
        try:
            account = self.trading_client.get_account()
            logger.debug(f"Account status: {account.status}")
            return account
        except APIError as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_buying_power(self) -> float:
        """
        Get available buying power.

        Returns:
            Available cash for trading

        Raises:
            APIError: If the API request fails
        """
        account = self.get_account()

        if account.trading_blocked:
            logger.warning("Account is restricted from trading")
            return 0.0

        buying_power = float(account.buying_power)
        logger.info(f"Available buying power: ${buying_power:,.2f}")
        return buying_power

    def is_tradeable(self) -> bool:
        """
        Check if the account can currently trade.

        Returns:
            True if account is not restricted, False otherwise
        """
        try:
            account = self.get_account()
            return not account.trading_blocked
        except APIError:
            return False

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get a summary of account metrics.

        Returns:
            Dictionary with key account metrics

        Raises:
            APIError: If the API request fails
        """
        account = self.get_account()

        summary = {
            "buying_power": float(account.buying_power),
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "equity": float(account.equity),
            "trading_blocked": account.trading_blocked,
            "account_status": account.status,
        }

        logger.info(f"Account summary: {summary}")
        return summary
