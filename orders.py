# ============================================================
# ФАЙЛ: orders.py
# Опис:
# Отримання відкритих ордерів з OKX.
# Якщо API не авторизований — бот НЕ падає.
#
# Виправлення:
# - Секрети беруться з environment variables (GitHub Secrets)
# - BASE_URL визначено локально
# - звужено блок except
# ============================================================

import os
import requests
import hmac
import base64
import hashlib
import time


# ------------------------------------------------------------
# Базовий URL OKX
# ------------------------------------------------------------
BASE_URL = "https://www.okx.com"


# ------------------------------------------------------------
# Отримання секретів з environment
# (GitHub Actions → Settings → Secrets)
# ------------------------------------------------------------
API_KEY = os.getenv("OKX_API_KEY")
API_SECRET = os.getenv("OKX_API_SECRET")
API_PASSPHRASE = os.getenv("OKX_API_PASSPHRASE")


# ------------------------------------------------------------
# Формування заголовків OKX API
# ------------------------------------------------------------
def _headers(method, request_path, body=""):

    if not API_KEY or not API_SECRET or not API_PASSPHRASE:
        return {}

    timestamp = str(time.time())

    message = timestamp + method + request_path + body

    mac = hmac.new(
        API_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    )

    sign = base64.b64encode(mac.digest()).decode()

    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json",
    }


# ------------------------------------------------------------
# Отримання найближчих ордерів
# ------------------------------------------------------------
def get_my_nearest_orders(symbol, price_now):

    path = f"/api/v5/trade/orders-pending?instId={symbol}&limit=50"
    url = BASE_URL + path

    try:
        r = requests.get(url, headers=_headers("GET", path), timeout=10)

        if r.status_code == 401:
            return [], []

        r.raise_for_status()

        data = r.json()

        if data.get("code") != "0":
            return [], []

        orders = data.get("data", [])

    except requests.RequestException:
        return [], []
    except ValueError:
        return [], []

    sells = []
    buys = []

    for o in orders:
        px = float(o["px"])
        sz = float(o["sz"])

        if px > price_now:
            sells.append((px, sz, abs(px - price_now)))
        else:
            buys.append((px, sz, abs(px - price_now)))

    sells = sorted(sells, key=lambda x: x[2])[:2]
    buys = sorted(buys, key=lambda x: x[2])[:2]

    return sells, buys
