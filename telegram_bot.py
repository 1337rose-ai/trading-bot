from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import requests
import os

load_dotenv()

MY_ID = int(os.getenv('TELEGRAM_USER_ID', '0'))
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

def notify(message):
    if not TOKEN or not MY_ID:
        print(f"Telegram not configured: {message}")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": MY_ID, "text": message})
        print(f"Notification sent: {message}")
    except Exception as e:
        print(f"Telegram notification failed: {e}")

def clear_telegram_session():
    """Force close any existing Telegram sessions before starting."""
    try:
        # Delete any existing webhook
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",
            json={"drop_pending_updates": True}
        )
        print("Cleared existing Telegram webhook/session.")
    except Exception as e:
        print(f"Clear session note: {e}")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return

    msg = update.message.text
    print(f"Received message: {msg}")
    await update.message.reply_text("Got it! Let me check that for you...")

    try:
        from agent import run_agent
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_agent, msg)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    print("Telegram bot starting...")

    # Clear any existing sessions first
    clear_telegram_session()

    # Wait a moment for Telegram to process the clearance
    import time
    time.sleep(3)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            print("Telegram bot running!")
            while True:
                await asyncio.sleep(1)

    loop.run_until_complete(run())

if __name__ == "__main__":
    main()