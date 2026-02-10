# ============================================================
# ФАЙЛ: exchange.py
# Опис:
# Отримання фʼючерсних свічок OKX
# Публічний market endpoint — без API ключів
# ============================================================

import requests

OKX_KLINES_URL = "https://www.okx.com/api/v5/market/history-candles"


def get_futures_klines(symbol: str, interval: str, limit: int):
    """
    Отримує свічки OKX Futures

    symbol  : BTC-USDT-SWAP
    interval: 1, 5
    limit   : кількість свічок
    """

    params = {
        "instId": symbol,
        "bar": interval + "m",
        "limit": limit,
    }

    r = requests.get(OKX_KLINES_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "0":
        raise RuntimeError(f"OKX API error: {data}")

    return data["data"]
