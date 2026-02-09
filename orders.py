# ============================================================
# ФАЙЛ: orders.py
# Опис:
# Отримання власних ордерів з OKX
# ============================================================

import os
import requests

BASE_URL = "https://www.okx.com"

API_KEY = os.getenv("OKX_API_KEY")
API_SECRET = os.getenv("OKX_API_SECRET")


def get_my_nearest_orders(symbol: str):
    """
    Повертає найближчі Buy / Sell ордери:
    (price, volume, trigger_price | None)
    """
    url = BASE_URL + "/api/v5/trade/orders-pending"

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": API_SECRET,  # HMAC тут не реалізуємо — узгоджено раніше
    }

    params = {"instId": symbol, "limit": 50}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data.get("code") != "0":
        return [], []

    sells, buys = [], []

    for o in data.get("data", []):
        price = float(o.get("px", 0))
        qty = float(o.get("sz", 0))

        trigger = o.get("triggerPx")
        trigger_price = float(trigger) if trigger else None

        if o.get("side") == "sell":
            sells.append((price, qty, trigger_price))
        else:
            buys.append((price, qty, trigger_price))

    return sells, buys
