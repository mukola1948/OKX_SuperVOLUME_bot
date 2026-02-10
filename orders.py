# ============================================================
# ФАЙЛ: orders.py
# Опис:
# Отримання власних ордерів з OKX
# Реалізовано повний HMAC-підпис (обовʼязково для private API)
# ============================================================

import os
import time
import hmac
import base64
import hashlib
import requests

BASE_URL = "https://www.okx.com"

API_KEY = os.getenv("OKX_API_KEY")
API_SECRET = os.getenv("OKX_API_SECRET")
API_PASSPHRASE = os.getenv("OKX_API_PASSPHRASE")


def _sign(ts: str, method: str, path: str) -> str:
    """
    Формує HMAC SHA256 підпис для OKX
    """
    msg = f"{ts}{method}{path}"
    mac = hmac.new(
        API_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()


def get_my_nearest_orders(symbol: str, current_price: float):
    """
    Повертає 2 найближчі SELL (вище ціни)
    та 2 найближчі BUY (нижче ціни)
    """

    path = f"/api/v5/trade/orders-pending?instId={symbol}&limit=50"
    ts = str(time.time())

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": _sign(ts, "GET", path),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
    }

    response = requests.get(BASE_URL + path, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data.get("code") != "0":
        return [], []

    sells, buys = [], []

    for o in data.get("data", []):
        price = float(o["px"])
        qty = float(o["sz"])
        trigger = o.get("triggerPx")
        trigger_price = float(trigger) if trigger else None

        record = (price, qty, trigger_price)

        if o["side"] == "sell" and price > current_price:
            sells.append(record)
        if o["side"] == "buy" and price < current_price:
            buys.append(record)

    sells.sort(key=lambda x: x[0])
    buys.sort(key=lambda x: x[0], reverse=True)

    return sells[:2], buys[:2]
