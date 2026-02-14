# ============================================================
# ФАЙЛ: main.py
# ============================================================

from config import PAIRS, INTERVALS, INIT_CANDLES
from exchange import get_futures_klines
from analyzer import analyze
from formatter import build_message
from telegram_sender import send
from state import load_state, save_state, get_last_ts, set_last_ts
from orders import get_my_nearest_orders


def run():

    state = load_state()

    for pair in PAIRS:
        for interval_label, interval_api in INTERVALS.items():

            last_ts = get_last_ts(state, pair)

            try:
                candles = get_futures_klines(pair, interval_api, INIT_CANDLES)
            except Exception as e:
                print(f"[WARN] Skip {pair}: {e}")
                continue

            candles = list(reversed(candles))

            if last_ts:
                candles = [c for c in candles if int(c[0]) > int(last_ts)]

            if not candles:
                continue

            analysis = analyze(candles)

            if analysis:

                candle = analysis["candle"]

                price_now = float(candle[4])
                spike_price = float(candle[2])

                try:
                    sells, buys = get_my_nearest_orders(pair, price_now)
                except Exception as e:
                    print(f"[WARN] Orders error {pair}: {e}")
                    sells, buys = [], []

                message = build_message(
                    symbol=pair,  # ← ВИПРАВЛЕНО (було pair.split)
                    interval_label=interval_label,
                    price_now=price_now,
                    vmax=analysis["vmax"],
                    cep_value=analysis["cep"],
                    ratio=analysis["ratio"],
                    is_green_candle=float(candle[4]) >= float(candle[1]),
                    vmax_candle_count=analysis["spike_count"],
                    cep_candle_count=len(candles),
                    spike_price=spike_price,
                    sells=sells,
                    buys=buys,
                )

                send(message)

            set_last_ts(state, pair, candles[-1][0])

    save_state(state)


if __name__ == "__main__":
    run()
