TRADING_TOOLS = [
    {
        "name": "get_account_balance",
        "description": "Get current wallet balance and available margin.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_market_price",
        "description": "Get the current market price for a trading symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair e.g. BTCUSDT"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "place_order",
        "description": "Place a market or limit order on ByBit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair e.g. BTCUSDT"
                },
                "side": {
                    "type": "string",
                    "enum": ["Buy", "Sell"]
                },
                "qty": {
                    "type": "number",
                    "description": "Order quantity"
                },
                "order_type": {
                    "type": "string",
                    "enum": ["Market", "Limit"]
                },
                "price": {
                    "type": "number",
                    "description": "Price for limit orders only"
                },
                "stop_loss": {
                    "type": "number",
                    "description": "Stop loss price"
                },
                "take_profit": {
                    "type": "number",
                    "description": "Take profit price"
                }
            },
            "required": ["symbol", "side", "qty", "order_type"]
        }
    },
    {
        "name": "close_position",
        "description": "Close an open position for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair e.g. BTCUSDT"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_open_positions",
        "description": "Get all currently open positions.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]