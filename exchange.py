# ============================================================
# ФАЙЛ: exchange.py
# ============================================================

import requests

OKX_KLINES_URL = "https://www.okx.com/api/v5/market/history-candles"


def get_futures_klines(symbol: str, interval: str, limit: int = None, after: str = None):
    params = {
        "instId": symbol,
        "bar": str(interval) + "m",
    }

    if limit is not None:
        params["limit"] = str(limit)

    if after is not None:
        params["after"] = str(after)

    r = requests.get(OKX_KLINES_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "0":
        raise RuntimeError(f"OKX API error: {data}")

    return data["data"]
