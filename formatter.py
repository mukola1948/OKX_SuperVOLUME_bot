# ============================================================
# ФАЙЛ: formatter.py
# Опис:
# Формування повідомлення Telegram
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
    price_now,
    ratio,
    is_green,
    spike_price,
    spike_ts,
    vmax,
    cep,
    sells,
    buys,
):

    token = symbol.split("-")[0]  # LDO-USDT-SWAP → LDO

    tz = timezone(timedelta(hours=2))
    spike_time = datetime.fromtimestamp(
        int(spike_ts) / 1000, tz
    ).strftime("%H:%M")

    emoji = "🟢" if is_green else "🔴"
    emojis = emoji * (1 if ratio <= 50 else 2 if ratio < 100 else 3)
    hilo = "ХАЙ" if is_green else "ЛОЙ"

    s1 = _fmt("🔴Sell", sells[0] if len(sells) > 0 else None)
    b1 = _fmt("🟢Buy", buys[0] if len(buys) > 0 else None)

    s2 = _fmt("🔴Sell", sells[1] if len(sells) > 1 else None)
    b2 = _fmt("🟢Buy", buys[1] if len(buys) > 1 else None)

    return (
        f"{emojis}{token}{emojis}={price_now}\n"
        f"{ratio:.1f} X     {hilo} = {spike_price:.3f}\n"
        f"(Vmax) {vmax:.0f} > {cep:.0f}\n"
        f"СПЛЕСК в {spike_time}\n"
        f"{s1}||{b1}\n"
        f"{s2}||{b2}"
    )
