import anthropic
from dotenv import load_dotenv
from tools import TRADING_TOOLS
from bybit_tools import execute_tool
import os

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

SYSTEM_PROMPT = """
You are an autonomous trading agent managing a ByBit futures account.

TRADE SETTINGS:
- Margin per trade: $25
- Leverage: 10x
- Notional position: $250
- Stop Loss: 1 percent from entry
- Take Profit: 2 percent from entry
- Trailing Stop: 0.5 percent
- Max daily loss: $10

RULES:
1. When a BUY or SELL signal arrives:
   a. Check for any open positions first.
   b. If a position exists, close it immediately.
   c. Check current market price.
   d. Calculate quantity as 250 divided by current price.
   e. Calculate SL and TP based on entry price.
   f. Place the order with SL, TP and trailing stop.

2. When a position closes at break-even (within 0.1 percent of entry):
   a. Check re-entry conditions using check_reentry_conditions tool.
   b. If price has moved 1 percent from original entry, place a re-entry order.
   c. Re-entry uses same entry price, SL, TP and trailing stop as original trade.
   d. Re-entry only happens once per signal.

3. If an opposing signal arrives while a re-entry order is pending:
   a. Cancel the re-entry order immediately using cancel_reentry tool.
   b. Then process the new signal normally.

4. Stop trading for the day if daily loss reaches $10.

5. Always summarise what you did after completing any action.

Be decisive. Act immediately. Do not ask for confirmation.
"""

def run_agent(signal, is_trade=False):
    print(f"\nAgent received: {signal}")

    from telegram_bot import notify

    if is_trade:
        notify(f"Signal received:\n{signal}\nAgent analyzing...")

    messages  = [{"role": "user", "content": signal}]
    final_text = ""

    for turn in range(15):
        print(f"Agent thinking... (turn {turn + 1})")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TRADING_TOOLS,
            messages=messages
        )

        tool_results = []

        for block in response.content:
            if block.type == "text":
                print(f"Agent: {block.text}")
                final_text = block.text

            elif block.type == "tool_use":
                print(f"Tool: {block.name} | Input: {block.input}")

                if is_trade and block.name == "place_order":
                    notify(
                        f"Placing order:\n"
                        f"Symbol: {block.input.get('symbol')}\n"
                        f"Side: {block.input.get('side')}\n"
                        f"Qty: {block.input.get('qty')}\n"
                        f"Stop Loss: {block.input.get('stop_loss')}\n"
                        f"Take Profit: {block.input.get('take_profit')}\n"
                        f"Trailing Stop: {block.input.get('trailing_stop', 0.5)}%"
                    )

                if is_trade and block.name == "place_reentry_order":
                    notify(
                        f"Re-entry order placed:\n"
                        f"Symbol: {block.input.get('symbol')}\n"
                        f"Side: {block.input.get('side')}\n"
                        f"Entry: {block.input.get('entry_price')}\n"
                        f"Stop Loss: {block.input.get('stop_loss')}\n"
                        f"Take Profit: {block.input.get('take_profit')}"
                    )

                if is_trade and block.name == "cancel_reentry":
                    notify(
                        f"Re-entry order cancelled.\n"
                        f"New opposing signal received."
                    )

                result = execute_tool(block.name, block.input)
                print(f"Result: {result}")

                if is_trade and block.name == "close_position":
                    notify(f"Position closed:\n{result}")

                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result
                })

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print("Agent completed.")
            if is_trade:
                notify(f"Agent completed:\n{final_text}")
            return final_text

        messages.append({"role": "user", "content": tool_results})

    return "Agent reached maximum turns."

if __name__ == "__main__":
    run_agent("Check my account balance.")