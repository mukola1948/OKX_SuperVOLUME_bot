# ============================================================
# ФАЙЛ: telegram_sender.py
# Опис:
# Відправка повідомлень у Telegram
# ============================================================

import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
