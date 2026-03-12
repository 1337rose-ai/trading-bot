import anthropic
from dotenv import load_dotenv
from tools import TRADING_TOOLS
from bybit_tools import execute_tool
import os

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

SYSTEM_PROMPT = """
You are an autonomous trading agent managing a ByBit futures account.

When given a trading signal or command, follow these rules:
1. Always check account balance before placing any trade.
2. Always check the current market price before entering.
3. Never risk more than 1 percent of account equity per trade.
4. Always include a stop loss on every order.
5. After executing, summarize exactly what you did.

Be decisive. Act on signals. Do not ask for confirmation.
"""

def run_agent(signal, is_trade=False):
    print(f"\nAgent received: {signal}")

    from telegram_bot import notify

    if is_trade:
        notify(
            f"Signal received:\n"
            f"{signal}\n"
            f"Agent is analyzing..."
        )

    messages = [{"role": "user", "content": signal}]
    final_text = ""

    for turn in range(10):
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
                print(f"Agent says: {block.text}")
                final_text = block.text
            elif block.type == "tool_use":
                print(f"Agent calling tool: {block.name} with {block.input}")

                if is_trade and block.name == "place_order":
                    notify(
                        f"Placing order:\n"
                        f"Symbol: {block.input.get('symbol')}\n"
                        f"Side: {block.input.get('side')}\n"
                        f"Qty: {block.input.get('qty')}\n"
                        f"Stop Loss: {block.input.get('stop_loss')}\n"
                        f"Take Profit: {block.input.get('take_profit')}"
                    )

                result = execute_tool(block.name, block.input)
                print(f"Tool result: {result}")

                if is_trade and block.name == "place_order":
                    notify(f"Order placed:\n{result}")

                if is_trade and block.name == "close_position":
                    notify(
                        f"Position closed:\n"
                        f"Symbol: {block.input.get('symbol')}\n"
                        f"Result: {result}"
                    )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print("Agent completed task.")
            if is_trade:
                notify(f"Trade completed:\n{final_text}")
            return final_text

        messages.append({"role": "user", "content": tool_results})

    return "Agent reached maximum turns."