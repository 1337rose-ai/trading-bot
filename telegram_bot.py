from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

MY_ID = int(os.getenv('TELEGRAM_USER_ID'))
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

app = ApplicationBuilder().token(TOKEN).build()

async def send_notification(message):
    await app.bot.send_message(chat_id=MY_ID, text=message)

def notify(message):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(send_notification(message))
        else:
            loop.run_until_complete(send_notification(message))
    except Exception as e:
        print(f"Telegram notification failed: {e}")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ID:
        return

    msg = update.message.text
    print(f"Received message: {msg}")

    await update.message.reply_text("Got it! Let me check that for you...")

    try:
        from agent import run_agent
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_agent, msg
        )
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    print("Telegram bot starting...")
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running! Send any message to your bot on Telegram.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()