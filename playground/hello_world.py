from dotenv import load_dotenv
load_dotenv()
import os
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_API_SECRET")

# %%
from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import ListAccountsRequest
from alpaca.broker.enums import AccountEntities
import datetime

broker_client = BrokerClient(api_key, api_secret)

# search for accounts created after January 30th 2022.
# Response should contain Contact and Identity fields for each account.
filter = ListAccountsRequest(
                    created_after=datetime.datetime.strptime("2022-01-30", "%Y-%m-%d"),
                    entities=[AccountEntities.CONTACT, AccountEntities.IDENTITY]
                    )

# accounts = broker_client.list_accounts(search_parameters=filter)
accounts = broker_client.list_accounts()

# %%
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest

trading_client = TradingClient(api_key, api_secret, paper=True)

# Get our account information.
account = trading_client.get_account()

# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check how much money we can use to open new positions.
print('${} is available as buying power.'.format(account.buying_power))
