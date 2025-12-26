"""
Order management utilities.

Provides functions to place, track, and manage orders with
proper error handling and logging.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order
from alpaca.common.exceptions import APIError


@dataclass
class BracketOrderParams:
    """
    Parameters for a bracket order (entry + take profit + stop loss).

    Attributes:
        symbol: Stock symbol
        notional: Dollar amount to invest
        take_profit_price: Price at which to take profit
        stop_loss_price: Price at which to stop loss
        side: Order side (buy/sell)
        time_in_force: Order time in force
    """

    symbol: str
    notional: float
    take_profit_price: float
    stop_loss_price: float
    side: OrderSide = OrderSide.BUY
    time_in_force: TimeInForce = TimeInForce.DAY


class OrderManager:
    """
    Manages order placement and tracking.

    Handles creation of market orders with bracket (take profit/stop loss)
    parameters.
    """

    def __init__(self, trading_client: TradingClient, logger: logging.Logger):
        """
        Initialize order manager.

        Args:
            trading_client: Alpaca trading client
            logger: Logger instance
        """
        self.trading_client = trading_client
        self.logger = logger

    def place_bracket_order(
        self, params: BracketOrderParams, dry_run: bool = False
    ) -> Optional[Order]:
        """
        Place a bracket order with take profit and stop loss.

        Args:
            params: Bracket order parameters
            dry_run: If True, log the order but don't place it

        Returns:
            Order object if successful, None otherwise

        Raises:
            APIError: If the API request fails (when not dry_run)
        """
        self.logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Placing bracket order: "
            f"{params.symbol} ${params.notional:.2f} notional, "
            f"TP=${params.take_profit_price:.2f}, "
            f"SL=${params.stop_loss_price:.2f}"
        )

        if dry_run:
            self.logger.info("Dry run mode: order not placed")
            return None

        try:
            # Place market order with notional amount (supports fractional shares)
            order_request = MarketOrderRequest(
                symbol=params.symbol,
                notional=params.notional,
                side=params.side,
                time_in_force=params.time_in_force,
                # Bracket orders: take_profit and stop_loss
                take_profit={"limit_price": params.take_profit_price},
                stop_loss={"stop_price": params.stop_loss_price},
            )

            order = self.trading_client.submit_order(order_request)

            self.logger.info(
                f"Order placed successfully: {order.id} - "
                f"{params.symbol} ${params.notional:.2f}"
            )

            return order

        except APIError as e:
            self.logger.error(
                f"Failed to place order for {params.symbol}: {e}",
                exc_info=True,
            )
            raise

    def place_market_order(
        self,
        symbol: str,
        notional: float,
        side: OrderSide = OrderSide.BUY,
        time_in_force: TimeInForce = TimeInForce.DAY,
        dry_run: bool = False,
    ) -> Optional[Order]:
        """
        Place a simple market order (no bracket).

        Args:
            symbol: Stock symbol
            notional: Dollar amount to invest
            side: Order side (buy/sell)
            time_in_force: Order time in force
            dry_run: If True, log the order but don't place it

        Returns:
            Order object if successful, None otherwise

        Raises:
            APIError: If the API request fails (when not dry_run)
        """
        self.logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Placing market order: "
            f"{symbol} ${notional:.2f} {side.value}"
        )

        if dry_run:
            self.logger.info("Dry run mode: order not placed")
            return None

        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=side,
                time_in_force=time_in_force,
            )

            order = self.trading_client.submit_order(order_request)

            self.logger.info(
                f"Order placed successfully: {order.id} - {symbol} ${notional:.2f}"
            )

            return order

        except APIError as e:
            self.logger.error(
                f"Failed to place order for {symbol}: {e}",
                exc_info=True,
            )
            raise

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        Get the status of an order.

        Args:
            order_id: Order ID

        Returns:
            Order object, or None if not found

        Raises:
            APIError: If the API request fails
        """
        try:
            order = self.trading_client.get_order_by_id(order_id)
            self.logger.debug(f"Order {order_id} status: {order.status}")
            return order
        except APIError as e:
            self.logger.error(f"Failed to get order status for {order_id}: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID

        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            self.logger.info(f"Order {order_id} cancelled successfully")
            return True
        except APIError as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
