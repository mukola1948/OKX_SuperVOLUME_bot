# ============================================================
# ФАЙЛ: main.py
# ============================================================

from config import PAIRS, INTERVAL, K_SPIKE
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

        # якщо state порожній → 100 свічок
        if not last_ts:
            candles = get_futures_klines(pair, INTERVAL, limit=100)
        else:
            candles = get_futures_klines(pair, INTERVAL, after=last_ts)

        if not candles:
            continue

        candles = list(reversed(candles))

        analysis = analyze(candles)
        if not analysis:
            set_last_ts(state, pair, candles[-1][0])
            continue

        if analysis["ratio"] >= K_SPIKE:

            spike_index = analysis["vmax_index"]
            spike_candle = candles[spike_index]

            spike_ts = spike_candle[0]
            price_now = float(spike_candle[4])

            if last_ts and spike_ts <= last_ts:
                continue

            sells, buys = get_my_nearest_orders(pair, price_now)

            message = build_message(
                symbol=pair,
                price_now=price_now,
                ratio=analysis["ratio"],
                is_green=analysis["is_green"],
                spike_price=analysis["spike_price"],
                spike_ts=spike_ts,
                vmax=analysis["vmax"],
                cep=analysis["cep"],
                sells=sells,
                buys=buys,
            )

            send(message)

            set_last_ts(state, pair, spike_ts)

        else:
            set_last_ts(state, pair, candles[-1][0])

    save_state(state)


if __name__ == "__main__":
    run()
