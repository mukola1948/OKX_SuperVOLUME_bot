"""
main.py

Головний файл бота.
"""

from config import PAIRS, INTERVAL, MIN_CANDLES
from exchange import get_futures_klines
from analyzer import analyze
from formatter import format_message
from notifier import notify
from state import load_state, save_state, get_last_ts, set_last_ts
from orders import get_my_nearest_orders


def run():

    state = load_state()

    for pair in PAIRS:

        last_ts = get_last_ts(state, pair)

        if not last_ts:
            candles = get_futures_klines(pair, INTERVAL, limit=MIN_CANDLES)
        else:
            candles = get_futures_klines(pair, INTERVAL, after=last_ts)

        if not candles:
            continue

        candles = list(reversed(candles))

        analysis = analyze(candles)

        if not analysis:
            if candles:
                set_last_ts(state, pair, candles[-1][0])
            continue

        spike_ts = analysis["spike_candle"][0]

        if last_ts and spike_ts <= last_ts:
            continue

        price = float(candles[-1][4])
        low_price = float(analysis["spike_candle"][3])

        sells, buys = get_my_nearest_orders(pair, price)

        message = format_message(
            pair,
            INTERVAL,
            price,
            analysis,
            low_price,
            sells,
            buys
        )

        notify(message)

        set_last_ts(state, pair, candles[-1][0])

    save_state(state)


if __name__ == "__main__":
    run()
