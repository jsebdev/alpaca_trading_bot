# %%
import logging
from dotenv import load_dotenv
load_dotenv()
import os
import sys
from pprint import pprint
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest

sys.path.insert(0, "../src")
from utils.logger import setup_logger
logger = setup_logger(name="hello_world_trading", level=logging.DEBUG)


# %%
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_API_SECRET")

# %%
trading_client = TradingClient(api_key, api_secret, paper=True)
account = trading_client.get_account()

print('>>>>> hello_world_trading.py:39 "account"')
pprint(account)
