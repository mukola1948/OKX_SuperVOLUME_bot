# ============================================================
# ФАЙЛ: formatter.py
# ============================================================

from datetime import datetime, timezone, timedelta

EMPTY = "-------------------"


def _fmt(label, order):
    if not order:
        return EMPTY
    price, qty, _ = order
    return f"{label}: {int(qty)}/{price:.4f}"


def build_message(
    symbol,
    interval_label,
    price_now,
    vmax,
    cep_value,
    ratio,
    is_green_candle,
    vmax_candle_count,
    cep_candle_count,
    spike_price,
    sells,
    buys,
):

    tz = timezone(timedelta(hours=2))
    time_str = datetime.now(tz).strftime("%H:%M / %d-%m")

    emoji = "🟢" if is_green_candle else "🔴"
    emojis = emoji * (1 if ratio <= 50 else 2 if ratio < 100 else 3)
    hilo = "ХАЙ" if is_green_candle else "ЛОЙ"

    s1 = _fmt("🔴Sell", sells[0] if len(sells) > 0 else None)
    b1 = _fmt("🟢Buy",  buys[0] if len(buys) > 0 else None)

    s2 = _fmt("🔴Sell", sells[1] if len(sells) > 1 else None)
    b2 = _fmt("🟢Buy",  buys[1] if len(buys) > 1 else None)

    return (
        f"{emojis}{symbol} {interval_label}{emojis} = {price_now}\n"
        f"{ratio:.1f} X     {hilo} = {spike_price:.3f}\n"
        f"(Vmax{vmax_candle_count}св) {vmax:.0f} > {cep_value:.0f} (Vсер.{cep_candle_count}св)\n"
        f"({time_str}) сплеск об'єм\n"
        f"{s1}||{b1}\n"
        f"{s2}||{b2}"
    )
