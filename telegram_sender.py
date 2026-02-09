# ============================================================
# ФАЙЛ: telegram_sender.py
# Опис:
# Відправка готового повідомлення в Telegram
# ============================================================

import os
import requests

def send_telegram_message(text: str):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("Telegram ENV variables not set")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
