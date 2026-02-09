# ============================================================
# ФАЙЛ: formatter.py
# Опис:
# Формування тексту для Telegram
# ============================================================

from datetime import datetime, timezone, timedelta
from typing import Optional


def _format_side(label: str, volume: Optional[float], price: Optional[float], trigger: Optional[float]):
    """
    Формат Buy / Sell:
    - якщо немає ордера → -------------------
    - після Buy / Sell НЕ ставити :
    - trigger показувати ТІЛЬКИ якщо існує
    """
    if volume is None or price is None:
        return "-------------------"

    if trigger is not None:
        return f"{label} {volume}/{price}/{trigger}"
    else:
        return f"{label} {volume}/{price}"


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
    sell_order: tuple | None = None,  # (price, qty, trigger)
    buy_order: tuple | None = None,   # (price, qty, trigger)
) -> str:

    utc_plus_2 = timezone(timedelta(hours=2))
    now_utc2 = datetime.now(utc_plus_2)
    time_str = now_utc2.strftime("%H:%M / %d-%m")

    if ratio <= 50:
        emoji_count = 1
    elif ratio < 100:
        emoji_count = 2
    else:
        emoji_count = 3

    candle_emoji = "🟢" if is_green_candle else "🔴"
    emojis = candle_emoji * emoji_count
    hi_lo_label = "ХАЙ" if is_green_candle else "ЛОЙ"

    sell_price, sell_qty, sell_trigger = sell_order if sell_order else (None, None, None)
    buy_price, buy_qty, buy_trigger = buy_order if buy_order else (None, None, None)

    sell_str = _format_side("🔴Sell", sell_qty, sell_price, sell_trigger)
    buy_str = _format_side("🟢Buy", buy_qty, buy_price, buy_trigger)

    orders_block = f"{sell_str} | | {buy_str}"

    message = (
        f"{emojis}{symbol} {interval_label}{emojis} = {price_now}\n"
        f"{ratio:.1f} X     {hi_lo_label} = {spike_price:.3f}\n"
        f"(Vmax{vmax_candle_count}св) {vmax:.1f} > {cep_value:.1f} (Vсер.{cep_candle_count}св)\n"
        f"({time_str}) сплеск об'єму\n"
        f"{orders_block}"
    )

    return message
