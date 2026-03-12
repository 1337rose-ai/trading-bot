from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

load_dotenv()

session = HTTP(
    testnet=os.getenv('TESTNET', 'false') == 'true',
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET')
)

MAX_QTY = float(os.getenv('MAX_ORDER_QTY', '0.01'))
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '50'))

def execute_tool(name, inputs):

    if name == 'get_account_balance':
        r = session.get_wallet_balance(accountType='UNIFIED')
        equity = r['result']['list'][0]['totalEquity']
        return f"Account equity: {equity} USDT"

    if name == 'get_market_price':
        r = session.get_tickers(category='linear', symbol=inputs['symbol'])
        price = r['result']['list'][0]['lastPrice']
        return f"Current price of {inputs['symbol']}: {price}"

    if name == 'place_order':
        qty = min(float(inputs['qty']), MAX_QTY)
        print(f"Placing {inputs['side']} order: {qty} {inputs['symbol']}")

        params = {
            'category': 'linear',
            'symbol': inputs['symbol'],
            'side': inputs['side'],
            'orderType': inputs['order_type'],
            'qty': str(qty),
        }

        if inputs.get('price'):
            params['price'] = str(inputs['price'])
        if inputs.get('stop_loss'):
            params['stopLoss'] = str(inputs['stop_loss'])
        if inputs.get('take_profit'):
            params['takeProfit'] = str(inputs['take_profit'])

        r = session.place_order(**params)
        return f"Order placed: {r}"

    if name == 'close_position':
        pos = session.get_positions(
            category='linear',
            symbol=inputs['symbol']
        )
        p = pos['result']['list'][0]

        if p['size'] == '0':
            return f"No open position found for {inputs['symbol']}"

        close_side = 'Sell' if p['side'] == 'Buy' else 'Buy'
        r = session.place_order(
            category='linear',
            symbol=inputs['symbol'],
            side=close_side,
            orderType='Market',
            qty=p['size'],
            reduceOnly=True
        )
        return f"Position closed: {r}"

    if name == 'get_open_positions':
        r = session.get_positions(
            category='linear',
            settleCoin='USDT'
        )
        open_pos = [p for p in r['result']['list'] if p['size'] != '0']
        if not open_pos:
            return "No open positions"
        result = ""
        for p in open_pos:
            result += f"{p['symbol']}: {p['side']} {p['size']} @ {p['avgPrice']}\n"
        return result

    return f"Unknown tool: {name}"