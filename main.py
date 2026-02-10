# ============================================================
# ФАЙЛ: main.py
# Опис:
# Центральний оркестратор OKX_VOLUME_bot
# ============================================================

from config import PAIRS, INTERVALS, K_SPIKE, INIT_CANDLES
from exchange import get_futures_klines
from analyzer import analyze
from formatter import build_message
from telegram_sender import send
from state import load_state, save_state, get_cep, set_cep
from orders import get_my_nearest_orders


def run():
    state = load_state()

    for pair in PAIRS:
        for interval_label, interval_api in INTERVALS.items():

            cep_old = get_cep(state, interval_label)

            try:
                candles = get_futures_klines(pair, interval_api, INIT_CANDLES)
            except Exception as e:
                print(f"[WARN] Skip {pair} {interval_label}: {e}")
                continue

            analysis = analyze(candles, cep_old)
            set_cep(state, interval_label, analysis["cep_new"])

            if cep_old and analysis["vmax"] >= cep_old * K_SPIKE:

                price_now = float(candles[-1][4])

                try:
                    sells, buys = get_my_nearest_orders(pair, price_now)
                except Exception as e:
                    print(f"[WARN] Orders error {pair}: {e}")
                    sells, buys = [], []

                nearest_sell = min(sells, key=lambda x: x[0]) if sells else None
                nearest_buy = max(buys, key=lambda x: x[0]) if buys else None

                message = build_message(
                    symbol=pair,
                    interval_label=interval_label,
                    price_now=price_now,
                    vmax=analysis["vmax"],
                    cep_value=cep_old,
                    ratio=analysis["ratio"],
                    is_green_candle=analysis["is_green"],
                    vmax_candle_count=analysis["vmax_count"],
                    cep_candle_count=analysis["cep_count"],
                    spike_price=analysis["spike_price"],
                    sell_order=nearest_sell,
                    buy_order=nearest_buy,
                )

                send(message)

    save_state(state)


if __name__ == "__main__":
    run()
