"""
Market data fetching and analysis utilities.

Provides functions to fetch historical market data and calculate
technical indicators like average candle size.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.exceptions import APIError


logger = logging.getLogger(__name__)


@dataclass
class CandleData:
    """
    Container for candle (bar) data.

    Attributes:
        open: Opening price
        high: High price
        low: Low price
        close: Closing price
        volume: Trading volume
        timestamp: Bar timestamp
    """

    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

    @property
    def candle_size(self) -> float:
        """Calculate the size (high - low) of this candle."""
        return self.high - self.low


class MarketDataFetcher:
    """
    Fetches and processes market data from Alpaca.

    Handles retrieval of historical bars and calculation of
    technical metrics like average candle size.
    """

    def __init__(self, data_client: StockHistoricalDataClient):
        """
        Initialize market data fetcher.

        Args:
            data_client: Alpaca data client instance
        """
        self.data_client = data_client

    def get_historical_bars(
        self,
        symbol: str,
        days: int,
        timeframe: TimeFrame = TimeFrame.Day,
    ) -> list[CandleData]:
        """
        Fetch historical bar data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            days: Number of days to look back
            timeframe: Bar timeframe (default: daily)

        Returns:
            List of CandleData objects

        Raises:
            APIError: If the API request fails
        """
        try:
            # Add extra days to ensure we get enough data
            # (accounting for weekends/holidays)
            end = datetime.now()
            start = end - timedelta(days=days * 2)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                feed='iex',  # Use free IEX feed instead of SIP to avoid subscription restrictions
            )

            bars = self.data_client.get_stock_bars(request)

            if symbol not in bars.data:
                logger.warning(f"No bar data found for {symbol}")
                return []

            candles = [
                CandleData(
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=float(bar.volume),
                    timestamp=bar.timestamp,
                )
                for bar in bars.data[symbol]
            ]

            # Return only the requested number of most recent bars
            candles = candles[-days:] if len(candles) > days else candles

            logger.info(
                f"Fetched {len(candles)} bars for {symbol} "
                f"(requested {days} days)"
            )

            return candles

        except APIError as e:
            logger.error(f"Failed to fetch bars for {symbol}: {e}")
            raise

    def calculate_average_candle_size(
        self, symbol: str, lookback_days: int
    ) -> Optional[float]:
        """
        Calculate average candle size (high - low) over N days.

        Args:
            symbol: Stock symbol
            lookback_days: Number of days to average over

        Returns:
            Average candle size, or None if insufficient data

        Raises:
            APIError: If the API request fails
        """
        candles = self.get_historical_bars(symbol, lookback_days)

        if len(candles) < lookback_days:
            logger.warning(
                f"Insufficient data for {symbol}: "
                f"got {len(candles)} bars, needed {lookback_days}"
            )
            return None

        avg_size = sum(c.candle_size for c in candles) / len(candles)

        logger.info(
            f"{symbol} average candle size ({lookback_days} days): ${avg_size:.2f}"
        )

        return avg_size

    def get_previous_close(self, symbol: str) -> Optional[float]:
        """
        Get the previous day's closing price.

        Args:
            symbol: Stock symbol

        Returns:
            Previous close price, or None if unavailable

        Raises:
            APIError: If the API request fails
        """
        candles = self.get_historical_bars(symbol, days=2)

        if len(candles) < 2:
            logger.warning(f"Insufficient data to get previous close for {symbol}")
            return None

        # Get the second-to-last candle (previous day)
        prev_close = candles[-2].close

        logger.info(f"{symbol} previous close: ${prev_close:.2f}")

        return prev_close

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price (latest close from most recent bar).

        Args:
            symbol: Stock symbol

        Returns:
            Current price, or None if unavailable

        Raises:
            APIError: If the API request fails
        """
        candles = self.get_historical_bars(symbol, days=1)

        if not candles:
            logger.warning(f"No price data available for {symbol}")
            return None

        current_price = candles[-1].close

        logger.info(f"{symbol} current price: ${current_price:.2f}")

        return current_price

    def get_gap_info(self, symbol: str) -> Optional[Tuple[float, float, float]]:
        """
        Get gap information: previous close, current open, and gap percentage.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (previous_close, current_open, gap_percent)
            or None if data unavailable

        Raises:
            APIError: If the API request fails
        """
        candles = self.get_historical_bars(symbol, days=4)

        if len(candles) < 2:
            return None

        prev_close = candles[-2].close
        current_open = candles[-1].open
        gap_percent = ((current_open - prev_close) / prev_close) * 100

        logger.info(
            f"{symbol} gap: prev_close=${prev_close:.2f}, "
            f"current_open=${current_open:.2f}, gap={gap_percent:.2f}%"
        )

        return prev_close, current_open, gap_percent
