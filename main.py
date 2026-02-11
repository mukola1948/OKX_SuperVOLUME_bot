# ============================================================
# ФАЙЛ: main.py
# ============================================================

import requests
from config import PAIRS, INTERVAL, K_SPIKE, INIT_CANDLES
from exchange import get_futures_klines
from analyzer import analyze
from formatter import build_message
from telegram_sender import send
from state import load_state, save_state, get_last_ts, set_last_ts
from orders import get_my_nearest_orders


def run():
    state = load_state()

    for pair in PAIRS:

        last_ts = get_last_ts(state, pair)

        if not last_ts:
            candles = get_futures_klines(pair, INTERVAL, limit=INIT_CANDLES)
        else:
            candles = get_futures_klines(pair, INTERVAL, after=last_ts)

        if not candles:
            continue

        candles = list(reversed(candles))

        for candle in candles:

            ts = candle[0]

            if last_ts and ts <= last_ts:
                continue

            analysis = analyze([candle], 1)

            cep = analysis["cep_new"]

            if cep and analysis["vmax"] >= cep * K_SPIKE:

                price_now = float(candle[4])

                try:
                    sells, buys = get_my_nearest_orders(pair, price_now)
                except (requests.RequestException, RuntimeError):
                    sells, buys = [], []

                message = build_message(
                    symbol=pair,
                    interval_label="1m",
                    price_now=price_now,
                    vmax=analysis["vmax"],
                    cep_value=cep,
                    ratio=analysis["ratio"],
                    is_green_candle=analysis["is_green"],
                    vmax_candle_count=analysis["vmax_count"],
                    cep_candle_count=analysis["cep_count"],
                    spike_price=analysis["spike_price"],
                    sells=sells,
                    buys=buys,
                )

                send(message)

            set_last_ts(state, pair, ts)

    save_state(state)


if __name__ == "__main__":
    run()
