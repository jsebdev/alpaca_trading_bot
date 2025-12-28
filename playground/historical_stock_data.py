# %%
# Auto-reload modules before executing code - great for development!
%load_ext autoreload
%autoreload 2

from datetime import datetime
import logging
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()
import os
import sys
from pprint import pprint
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest

sys.path.insert(0, "../src")
from utils.logger import setup_logger
from utils.plot_candlestick_chart import plot_candlestick_chart
logger = setup_logger(name="hello_world_trading", level=logging.DEBUG)


# %%
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_API_SECRET")

# %%
client = StockHistoricalDataClient(api_key, api_secret)

# %%
symbols = ["AAPL", "MSFT"]

# %%
latest_quote_data_request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
latest_quote_data = client.get_stock_latest_quote(latest_quote_data_request)
print('>>>>> historical_stock_data.py:26 "latest_quote_data"')
print(latest_quote_data)

# %%
bars_request = StockBarsRequest(
    symbol_or_symbols=symbols,
    timeframe=TimeFrame.Day,
    start=datetime(2025, 12, 1),
)
bars_data = client.get_stock_bars(bars_request)

# %%
bars_df = bars_data.df
bars_df

# %%
plot_candlestick_chart(bars_df.xs("AAPL", level="symbol"))

# %%
plot_candlestick_chart(bars_df.xs("MSFT", level="symbol"))
