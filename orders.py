# ============================================================
# ФАЙЛ: orders.py
# Опис:
# Отримання ВЛАСНИХ ордерів (long / short) з OKX
# Використовується private API з HMAC-підписом
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
    Формування HMAC SHA256 підпису для private OKX API
    """
    msg = f"{ts}{method}{path}"
    mac = hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()


def get_my_nearest_orders(symbol: str, current_price: float):
    """
    Повертає:
    - 2 найближчі SELL (short) вище ціни
    - 2 найближчі BUY (long) нижче ціни
    Якщо ордерів немає — повертаються порожні списки
    """

    path = f"/api/v5/trade/orders-pending?instId={symbol}&limit=50"
    ts = str(time.time())

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": _sign(ts, "GET", path),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
    }

    r = requests.get(BASE_URL + path, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "0":
        return [], []

    sells, buys = [], []

    for o in data.get("data", []):
        price = float(o["px"])
        qty = float(o["sz"])
        trigger = float(o["triggerPx"]) if o.get("triggerPx") else None

        record = (price, qty, trigger)

        if o["side"] == "sell" and price > current_price:
            sells.append(record)

        if o["side"] == "buy" and price < current_price:
            buys.append(record)

    sells.sort(key=lambda x: x[0])          # ближчі SELL
    buys.sort(key=lambda x: x[0], reverse=True)  # ближчі BUY

    return sells[:2], buys[:2]
