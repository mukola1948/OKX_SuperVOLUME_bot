"""
formatter.py

Формує повідомлення для Telegram.

Зміни:
- відображається реальна кількість свічок
- відображається час останньої свічки (UTC+2)
- відображається час сплеску Vmax (UTC+2)
"""

from datetime import datetime, timezone, timedelta

EMPTY = "-------------------"


def _fmt(label, order):
    if not order:
        return EMPTY
    price, qty, _ = order
    return f"{label}: {int(qty)}/{price:.4f}"


def _short_symbol(symbol: str) -> str:
    return symbol.split("-")[0]


def _emoji_count(ratio: float) -> int:
    if ratio <= 50:
        return 1
    elif 50 < ratio < 100:
        return 2
    else:
        return 3


def _format_time_from_ts(ts: int):
    tz = timezone(timedelta(hours=2))
    dt = datetime.fromtimestamp(int(ts) / 1000, tz)
    return dt.strftime("%H:%M"), dt.strftime("%d-%m")


def build_message(
    symbol: str,
    interval_label: str,
    price_now: float,
    vmax: float,
    cep_value: float,
    ratio: float,
    is_green_candle: bool,
    vmax_candle_count: int,
    cep_candle_count: int,
    spike_price: float,
    spike_ts: int,
    last_candle_ts: int,
    sells: list,
    buys: list,
) -> str:

    short_symbol = _short_symbol(symbol)

    emoji = "🟢" if is_green_candle else "🔴"
    emojis = emoji * _emoji_count(ratio)

    hilo = "ХАЙ" if is_green_candle else "ЛОЙ"

    ratio_str = f"{ratio:.1f}".replace(".", ",")

    last_time, date_str = _format_time_from_ts(last_candle_ts)
    spike_time, _ = _format_time_from_ts(spike_ts)

    s1 = _fmt("🔴Sell", sells[0] if len(sells) > 0 else None)
    b1 = _fmt("🟢Buy", buys[0] if len(buys) > 0 else None)

    s2 = _fmt("🔴Sell", sells[1] if len(sells) > 1 else None)
    b2 = _fmt("🟢Buy", buys[1] if len(buys) > 1 else None)

    return (
        f"{emojis}{short_symbol} {interval_label}= {price_now}{emojis}\n"
        f"{ratio_str} X     {hilo} = {spike_price:.3f}\n"
        f"(Vmax{vmax_candle_count}св) {vmax:.0f} > {cep_value:.0f} (Vсер.{cep_candle_count}св)\n"
        f"({last_time} / {date_str}) СПЛЕСК {spike_time}\n"
        f"{s1}||{b1}\n"
        f"{s2}||{b2}"
    )
