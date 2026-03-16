from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from agent import run_agent
from telegram_bot import notify, send_message
import requests
import os

load_dotenv()

SECRET       = os.getenv('WEBHOOK_SECRET')
TOKEN        = os.getenv('TELEGRAM_BOT_TOKEN', '')
MY_ID        = int(os.getenv('TELEGRAM_USER_ID', '0'))
RAILWAY_URL  = os.getenv('RAILWAY_URL', '')

def register_telegram_webhook():
    if not RAILWAY_URL:
        print("RAILWAY_URL not set — Telegram webhook not registered")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    webhook_url = f"{RAILWAY_URL}/telegram"
    r = requests.post(url, json={
        "url": webhook_url,
        "drop_pending_updates": True
    })
    print(f"Telegram webhook registered: {r.json()}")

@asynccontextmanager
async def lifespan(app):
    register_telegram_webhook()
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "Bot is running"}

@app.post("/telegram")
async def telegram_webhook(request: Request, bg: BackgroundTasks):
    body = await request.json()
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    text    = message.get("text", "")

    if not text or not chat_id:
        return {"ok": True}

    if user_id != MY_ID:
        return {"ok": True}

    if text.startswith("/"):
        return {"ok": True}

    print(f"Received message: {text}")
    send_message(chat_id, "Got it! Let me check that for you...")

    def handle():
        result = run_agent(text)
        send_message(chat_id, result)

    bg.add_task(handle)
    return {"ok": True}

@app.post("/signal")
async def receive_signal(request: Request, bg: BackgroundTasks):
    body = await request.json()

    if body.get('secret') != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    symbol    = body.get('symbol', 'BTCUSDT')
    action    = body.get('action', '').upper()
    price     = body.get('price', 'market price')
    timeframe = body.get('timeframe', 'unknown')

    if action not in ['BUY', 'SELL']:
        raise HTTPException(status_code=400, detail="Invalid action")

    if action == 'BUY':
        signal = (
            f"NitrosBull BUY signal received.\n"
            f"Symbol: {symbol}\n"
            f"Price: {price}\n"
            f"Timeframe: {timeframe}\n"
            f"Instructions:\n"
            f"Step 1 - Check for any open positions on {symbol}. "
            f"If a position exists close it immediately.\n"
            f"Step 2 - Cancel any pending re-entry orders.\n"
            f"Step 3 - Check current market price of {symbol}.\n"
            f"Step 4 - Place BUY market order:\n"
            f"  Quantity = 250 divided by current price\n"
            f"  Stop Loss = 1.2 percent below entry\n"
            f"  Take Profit = 2.4 percent above entry\n"
            f"  Trailing Stop = 1 percent\n"
            f"  Max loss: $3.00 | Target profit: $6.00"
        )
    else:
        signal = (
            f"NitrosBull SELL signal received.\n"
            f"Symbol: {symbol}\n"
            f"Price: {price}\n"
            f"Timeframe: {timeframe}\n"
            f"Instructions:\n"
            f"Step 1 - Check for any open positions on {symbol}. "
            f"If a position exists close it immediately.\n"
            f"Step 2 - Cancel any pending re-entry orders.\n"
            f"Step 3 - Check current market price of {symbol}.\n"
            f"Step 4 - Place SELL market order:\n"
            f"  Quantity = 250 divided by current price\n"
            f"  Stop Loss = 1.2 percent above entry\n"
            f"  Take Profit = 2.4 percent below entry\n"
            f"  Trailing Stop = 1 percent\n"
            f"  Max loss: $3.00 | Target profit: $6.00"
        )

    bg.add_task(run_agent, signal, True)

    return {
        "status": "Signal received",
        "symbol": symbol,
        "action": action,
        "agent":  "running"
    }

@app.post("/command")
async def manual_command(request: Request, bg: BackgroundTasks):
    body = await request.json()

    if body.get('secret') != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    command = body.get('command', '')
    if not command:
        raise HTTPException(status_code=400, detail="No command provided")

    bg.add_task(run_agent, command)
    return {"status": "Command received", "command": command, "agent": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)