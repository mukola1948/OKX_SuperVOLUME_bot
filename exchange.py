# ============================================================
# ФАЙЛ: exchange.py
# Опис:
# Отримання свічок (klines) з OKX через API
# ============================================================

import os
import requests

OKX_KLINES_URL = "https://www.okx.com/api/v5/market/history-candles"

def get_futures_klines(symbol: str, interval: str, limit: int):
    """
    Отримує свічки OKX Futures

    symbol  : "BTCUSDT"
    interval: "1", "5"
    limit   : кількість свічок
    """
    api_key = os.getenv("OKX_API_KEY")
    api_secret = os.getenv("OKX_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError("OKX API credentials not set in ENV")

    params = {
        "instId": symbol,
        "bar": interval + "m",
        "limit": limit,
    }

    response = requests.get(OKX_KLINES_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "0":
        raise RuntimeError(f"OKX API error: {data}")

    return data["data"]
