# %%
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging

logging.basicConfig(level=logging.DEBUG, filemode='w', filename='app.log')

logger = logging.getLogger(__name__)

# no keys required for crypto data
client = CryptoHistoricalDataClient()

request_params = CryptoBarsRequest(
                        symbol_or_symbols=["BTC/USD", "ETH/USD"],
                        timeframe=TimeFrame.Day,
                        start="2022-07-01"
                 )

bars = client.get_crypto_bars(request_params)

# %%

# type(bars)
bars.keys()
