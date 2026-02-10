# ============================================================
# ФАЙЛ: exchange.py
# Опис:
# Отримання свічок (klines) з OKX
# Публічний endpoint — БЕЗ API ключів
# ============================================================

import requests

OKX_KLINES_URL = "https://www.okx.com/api/v5/market/history-candles"


def get_futures_klines(symbol: str, interval: str, limit: int):
    """
    Отримує свічки OKX Futures

    symbol  : "BTC-USDT-SWAP"
    interval: "1", "5"
    limit   : кількість свічок
    """

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
