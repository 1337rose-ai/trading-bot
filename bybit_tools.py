from pybit.unified_trading import HTTP
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import os

load_dotenv()

session = HTTP(
    testnet=os.getenv('TESTNET', 'false') == 'true',
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET')
)

MAX_NOTIONAL_USD = float(os.getenv('MAX_NOTIONAL_USD', '250'))
MAX_DAILY_LOSS   = float(os.getenv('MAX_DAILY_LOSS', '10'))
LEVERAGE         = os.getenv('LEVERAGE', '10')
SAST_OFFSET      = timedelta(hours=2)

daily_loss       = 0.0
last_reset       = datetime.now(timezone.utc)
last_signal      = None
last_entry_price = None
last_sl          = None
last_tp          = None
reentry_done     = False
reentry_order_id = None

def check_and_reset_daily_loss():
    global daily_loss, last_reset
    now       = datetime.now(timezone.utc)
    sast_now  = now + SAST_OFFSET
    sast_last = last_reset + SAST_OFFSET
    if sast_now.date() > sast_last.date():
        print(f"Resetting daily loss. Previous: ${daily_loss}")
        daily_loss = 0.0
        last_reset = now

def is_daily_limit_reached():
    check_and_reset_daily_loss()
    if daily_loss >= MAX_DAILY_LOSS:
        print(f"Daily loss limit reached: ${daily_loss}/${MAX_DAILY_LOSS}")
        return True
    return False

def record_loss(amount):
    global daily_loss
    daily_loss += abs(amount)
    print(f"Daily loss: ${daily_loss}/${MAX_DAILY_LOSS}")

def set_leverage(symbol):
    try:
        session.set_leverage(
            category='linear',
            symbol=symbol,
            buyLeverage=LEVERAGE,
            sellLeverage=LEVERAGE
        )
        print(f"Leverage set to {LEVERAGE}x")
    except Exception as e:
        print(f"Leverage note: {e}")

def get_current_price(symbol):
    r = session.get_tickers(category='linear', symbol=symbol)
    return float(r['result']['list'][0]['lastPrice'])

def calculate_qty(symbol):
    price = get_current_price(symbol)
    qty   = round(MAX_NOTIONAL_USD / price, 3)
    print(f"Calculated qty: {qty} (${MAX_NOTIONAL_USD} / ${price})")
    return qty

def cancel_reentry_order(symbol):
    global reentry_order_id
    if reentry_order_id:
        try:
            session.cancel_order(
                category='linear',
                symbol=symbol,
                orderId=reentry_order_id
            )
            print(f"Re-entry order cancelled: {reentry_order_id}")
            reentry_order_id = None
        except Exception as e:
            print(f"Cancel re-entry error: {e}")

def execute_tool(name, inputs):
    global last_signal, last_entry_price, last_sl, last_tp
    global reentry_done, reentry_order_id

    if name == 'get_account_balance':
        r      = session.get_wallet_balance(accountType='UNIFIED')
        equity = r['result']['list'][0]['totalEquity']
        return f"Account equity: {equity} USDT"

    if name == 'get_market_price':
        price = get_current_price(inputs['symbol'])
        return f"Current price of {inputs['symbol']}: {price}"

    if name == 'get_open_positions':
        r        = session.get_positions(category='linear', settleCoin='USDT')
        open_pos = [p for p in r['result']['list'] if p['size'] != '0']
        if not open_pos:
            return "No open positions"
        result = ""
        for p in open_pos:
            result += (
                f"{p['symbol']}: {p['side']} {p['size']} "
                f"@ {p['avgPrice']} | "
                f"Unrealised PnL: {p['unrealisedPnl']}\n"
            )
        return result

    if name == 'place_order':
        if is_daily_limit_reached():
            return f"Daily loss limit of ${MAX_DAILY_LOSS} reached. No more trades today."

        symbol        = inputs['symbol']
        side          = inputs['side']
        qty           = calculate_qty(symbol)
        entry_price   = float(inputs.get('price', 0))
        sl_price      = float(inputs.get('stop_loss', 0))
        tp_price      = float(inputs.get('take_profit', 0))
        trailing_stop = str(inputs.get('trailing_stop', '1'))

        set_leverage(symbol)

        last_signal      = side
        last_entry_price = entry_price
        last_sl          = sl_price
        last_tp          = tp_price
        reentry_done     = False
        reentry_order_id = None

        position_idx = 1 if side == 'Buy' else 2

        params = {
            'category':    'linear',
            'symbol':      symbol,
            'side':        side,
            'orderType':   'Market',
            'qty':         str(qty),
            'positionIdx': position_idx,
        }
        if sl_price:
            params['stopLoss']    = str(sl_price)
            params['slTriggerBy'] = 'MarkPrice'
        if tp_price:
            params['takeProfit']  = str(tp_price)
            params['tpTriggerBy'] = 'MarkPrice'
        if trailing_stop:
            params['trailingStop'] = str(trailing_stop)
            params['tpslMode'] = 'Full'

        r = session.place_order(**params)
        print(f"Order placed: {r}")
        return f"Order placed: {r}"

    if name == 'close_position':
        symbol        = inputs['symbol']
        pos           = session.get_positions(category='linear', symbol=symbol)
        p             = pos['result']['list'][0]

        if p['size'] == '0':
            return f"No open position for {symbol}"

        entry_price   = float(p['avgPrice'])
        current_price = get_current_price(symbol)
        side          = p['side']

        if side == 'Buy':
            pnl = (current_price - entry_price) / entry_price * MAX_NOTIONAL_USD
        else:
            pnl = (entry_price - current_price) / entry_price * MAX_NOTIONAL_USD

        if pnl < 0:
            record_loss(abs(pnl))

        breakeven_range = entry_price * 0.001
        is_breakeven    = abs(current_price - entry_price) <= breakeven_range

        close_side = 'Sell' if side == 'Buy' else 'Buy'
        close_position_idx = 1 if side == 'Buy' else 2
        r = session.place_order(
            category='linear',
            symbol=symbol,
            side=close_side,
            orderType='Market',
            qty=p['size'],
            positionIdx=close_position_idx,
            reduceOnly=True
        )

        result = f"Position closed. PnL: ${pnl:.2f}"

        if is_breakeven and not reentry_done and last_signal:
            result += " | Break-even exit detected. Monitoring for re-entry..."
            print("Break-even exit detected.")

        return result

    if name == 'place_reentry_order':
        if reentry_done:
            return "Re-entry already used for this signal."
        if is_daily_limit_reached():
            return "Daily loss limit reached. No re-entry."

        symbol        = inputs['symbol']
        side          = inputs['side']
        entry_price   = float(inputs['entry_price'])
        sl_price      = float(inputs['stop_loss'])
        tp_price      = float(inputs['take_profit'])
        qty           = calculate_qty(symbol)
        trailing_stop = str(inputs.get('trailing_stop', '1'))

        set_leverage(symbol)

        params = {
            'category':     'linear',
            'symbol':       symbol,
            'side':         side,
            'orderType':    'Limit',
            'triggerBy':    'MarkPrice',
            'triggerPrice': str(entry_price),
            'price':        str(entry_price),
            'qty':          str(qty),
            'stopLoss':     str(sl_price),
            'slTriggerBy':  'MarkPrice',
            'takeProfit':   str(tp_price),
            'tpTriggerBy':  'MarkPrice',
            'trailingStop': str(trailing_stop),
            'tpslMode':     'Full',,
            'timeInForce':  'GTC',
        }

        r                = session.place_order(**params)
        reentry_order_id = r['result'].get('orderId')
        reentry_done     = True
        print(f"Re-entry order placed: {reentry_order_id}")
        return f"Re-entry order placed at {entry_price}. Order ID: {reentry_order_id}"

    if name == 'cancel_reentry':
        cancel_reentry_order(inputs['symbol'])
        return "Re-entry order cancelled."

    if name == 'check_reentry_conditions':
        symbol        = inputs['symbol']
        current_price = float(inputs['current_price'])

        if not last_signal or not last_entry_price:
            return "no_reentry|No previous signal stored"
        if reentry_done:
            return "no_reentry|Re-entry already used"
        if is_daily_limit_reached():
            return "no_reentry|Daily loss limit reached"

        move_pct = abs(current_price - last_entry_price) / last_entry_price * 100
        if move_pct >= 1.0:
            return (
                f"reentry_valid|"
                f"side={last_signal}|"
                f"entry={last_entry_price}|"
                f"sl={last_sl}|"
                f"tp={last_tp}"
            )
        return f"no_reentry|Price only moved {move_pct:.2f}% from entry (need 1%)"

    return f"Unknown tool: {name}"
