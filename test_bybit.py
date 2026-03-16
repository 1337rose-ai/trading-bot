from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

load_dotenv()

session = HTTP(testnet=False, api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

balance = session.get_wallet_balance(accountType='UNIFIED')
print("Connected! Equity:", balance['result']['list'][0]['totalEquity'])