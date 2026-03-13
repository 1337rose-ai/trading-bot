from dotenv import load_dotenv
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

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Send message failed: {e}")