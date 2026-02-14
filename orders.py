# ============================================================
# ФАЙЛ: orders.py
# Опис:
# Отримання найближчих відкритих ф’ючерсних ордерів (SWAP)
# ============================================================

import os
import hmac
import base64
import hashlib
import requests
from datetime import datetime, timezone

BASE_URL = "https://www.okx.com"

API_KEY = os.getenv("OKX_API_KEY")
API_SECRET = os.getenv("OKX_API_SECRET")
API_PASSPHRASE = os.getenv("OKX_API_PASSPHRASE")


# ------------------------------------------------------------
# Генерація ISO-8601 timestamp (вимога OKX v5)
# ------------------------------------------------------------
def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ------------------------------------------------------------
# Підпис запиту згідно специфікації OKX v5
# ------------------------------------------------------------
def _sign(ts: str, method: str, path: str) -> str:
    message = f"{ts}{method}{path}"
    mac = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()


# ------------------------------------------------------------
# Отримання найближчих ордерів
# ------------------------------------------------------------
def get_my_nearest_orders(symbol: str, current_price: float):

    path = f"/api/v5/trade/orders-pending?instType=SWAP&instId={symbol}&limit=50"
    ts = _timestamp()

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": _sign(ts, "GET", path),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json",
    }

    r = requests.get(BASE_URL + path, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "0":
        print("[ORDERS ERROR]", data)
        return [], []

    sells, buys = [], []

    for o in data.get("data", []):
        price = float(o["px"]) if o.get("px") else 0
        qty = float(o["sz"])
        trigger = float(o["triggerPx"]) if o.get("triggerPx") else None

        record = (price, qty, trigger)

        if o["side"] == "sell" and price > current_price:
            sells.append(record)

        if o["side"] == "buy" and price < current_price:
            buys.append(record)

    sells.sort(key=lambda x: x[0])
    buys.sort(key=lambda x: x[0], reverse=True)

    return sells[:2], buys[:2]
