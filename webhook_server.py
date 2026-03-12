from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from agent import run_agent
import threading
import os

load_dotenv()

SECRET = os.getenv('WEBHOOK_SECRET')

@asynccontextmanager
async def lifespan(app):
    from telegram_bot import main as start_telegram
    telegram_thread = threading.Thread(target=start_telegram, daemon=True)
    telegram_thread.start()
    print("Telegram bot started!")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "Bot is running"}

@app.post("/signal")
async def receive_signal(request: Request, bg: BackgroundTasks):
    body = await request.json()

    if body.get('secret') != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    symbol = body.get('symbol', 'BTCUSDT')
    action = body.get('action', '').upper()
    price = body.get('price', 'market price')
    timeframe = body.get('timeframe', 'unknown')

    if action not in ['BUY', 'SELL']:
        raise HTTPException(status_code=400, detail="Invalid action")

    if action == 'BUY':
        signal = (
            f"NitrosBull BUY signal received.\n"
            f"Symbol: {symbol}\n"
            f"Price: {price}\n"
            f"Timeframe: {timeframe}\n"
            f"Instructions: Check account balance, check current market price, "
            f"then place a BUY market order on {symbol}. "
            f"Size the position at 1 percent of account equity. "
            f"Set a stop loss 2 percent below entry price. "
            f"Set a take profit 4 percent above entry price. "
            f"Follow all risk management rules."
        )
    elif action == 'SELL':
        signal = (
            f"NitrosBull SELL signal received.\n"
            f"Symbol: {symbol}\n"
            f"Price: {price}\n"
            f"Timeframe: {timeframe}\n"
            f"Instructions: Check account balance, check current market price, "
            f"then place a SELL market order on {symbol}. "
            f"Size the position at 1 percent of account equity. "
            f"Set a stop loss 2 percent above entry price. "
            f"Set a take profit 4 percent below entry price. "
            f"Follow all risk management rules."
        )

    bg.add_task(run_agent, signal, True)

    return {
        "status": "Signal received",
        "symbol": symbol,
        "action": action,
        "agent": "running"
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

    return {
        "status": "Command received",
        "command": command,
        "agent": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)