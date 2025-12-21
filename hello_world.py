from dotenv import load_dotenv
load_dotenv()


import os
from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import ListAccountsRequest
from alpaca.broker.enums import AccountEntities
import datetime

api_key = os.getenv("ALPACA_API_KEY")

api_secret = os.getenv("ALPACA_API_SECRET")

broker_client = BrokerClient(api_key, api_secret)

# search for accounts created after January 30th 2022.
# Response should contain Contact and Identity fields for each account.
filter = ListAccountsRequest(
                    created_after=datetime.datetime.strptime("2022-01-30", "%Y-%m-%d"),
                    entities=[AccountEntities.CONTACT, AccountEntities.IDENTITY]
                    )

# accounts = broker_client.list_accounts(search_parameters=filter)
accounts = broker_client.list_accounts()

print('>>>>> hello_world.py:26 "accounts"')
print(accounts)
