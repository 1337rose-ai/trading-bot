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
        "description": "Get the current market price for a symbol.",
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
        "description": "Place a market order on ByBit with SL, TP and trailing stop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol":        { "type": "string" },
                "side":          { "type": "string", "enum": ["Buy", "Sell"] },
                "qty":           { "type": "number" },
                "price":         { "type": "number", "description": "Entry price for reference" },
                "stop_loss":     { "type": "number" },
                "take_profit":   { "type": "number" },
                "trailing_stop": { "type": "number", "description": "Trailing stop percentage e.g. 0.5" }
            },
            "required": ["symbol", "side", "qty", "price", "stop_loss", "take_profit"]
        }
    },
    {
        "name": "close_position",
        "description": "Close an open position for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": { "type": "string" }
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
    },
    {
        "name": "check_reentry_conditions",
        "description": "Check if conditions are met for a re-entry order after a break-even exit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol":        { "type": "string" },
                "current_price": { "type": "number" }
            },
            "required": ["symbol", "current_price"]
        }
    },
    {
        "name": "place_reentry_order",
        "description": "Place a re-entry stop order at the original entry price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol":        { "type": "string" },
                "side":          { "type": "string", "enum": ["Buy", "Sell"] },
                "qty":           { "type": "number" },
                "entry_price":   { "type": "number" },
                "stop_loss":     { "type": "number" },
                "take_profit":   { "type": "number" },
                "trailing_stop": { "type": "number" }
            },
            "required": ["symbol", "side", "qty", "entry_price", "stop_loss", "take_profit"]
        }
    },
    {
        "name": "cancel_reentry",
        "description": "Cancel a pending re-entry stop order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": { "type": "string" }
            },
            "required": ["symbol"]
        }
    }
]
