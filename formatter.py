# ============================================================
# ФАЙЛ: formatter.py
# Опис:
# Формує фінальне повідомлення Telegram.
#
# Зміни:
# - використовується коротка назва токена (LDO, BTC, OP, ETH)
# - немає пробілу перед =
# - замість Vmax виводиться ratio
# - текст: СПЛЕСК в HH:MM
# - додана логіка 1-3 емодзі залежно від ratio
# - додана логіка кольору свічки
# - замість заглушки виводяться реальні ордери
# ============================================================

from datetime import datetime, UTC


# ------------------------------------------------------------
# Скорочення торгової пари (BTC-USDT → BTC)
# ------------------------------------------------------------
def shorten_pair(pair):
    return pair.split("-")[0]


# ------------------------------------------------------------
# Формування тексту ордерів
# ------------------------------------------------------------
def format_orders_block(sells, buys):

    lines = []

    # SELL ордери (вище ціни)
    if sells:
        lines.append("SELL ордери:")
        for px, sz, _ in sells:
            lines.append(f"  {px} | {sz}")

    # BUY ордери (нижче ціни)
    if buys:
        lines.append("BUY ордери:")
        for px, sz, _ in buys:
            lines.append(f"  {px} | {sz}")

    if not lines:
        return "Ордерів не знайдено"

    return "\n".join(lines)


# ------------------------------------------------------------
# Основне формування повідомлення
# ------------------------------------------------------------
def format_message(pair, interval, price, analysis, low_price, sells=None, buys=None):

    token = shorten_pair(pair)

    cep = analysis["cep"]
    vmax = analysis["vmax"]
    ratio = analysis["ratio"]
    spike_candle = analysis["spike_candle"]
    count = analysis["count"]

    # --------------------------------------------------------
    # Визначення кольору свічки
    # --------------------------------------------------------
    open_price = float(spike_candle[1])
    close_price = float(spike_candle[4])
    is_green_candle = close_price >= open_price

    # --------------------------------------------------------
    # 2. ЕМОДЗІ: кількість + колір
    # --------------------------------------------------------
    if ratio <= 50:
        emoji_count = 1
    elif ratio < 100:
        emoji_count = 2
    else:
        emoji_count = 3

    candle_emoji = "🟢" if is_green_candle else "🔴"
    emojis = candle_emoji * emoji_count

    hi_lo_label = "ХАЙ" if is_green_candle else "ЛОЙ"

    # --------------------------------------------------------
    # Час сплеску
    # --------------------------------------------------------
    ts = int(spike_candle[0])
    dt = datetime.fromtimestamp(ts / 1000, UTC)
    time_str = dt.strftime("%H:%M")

    # --------------------------------------------------------
    # Ордери
    # --------------------------------------------------------
    sells = sells or []
    buys = buys or []
    orders_block = format_orders_block(sells, buys)

    # --------------------------------------------------------
    # Формування повідомлення
    # --------------------------------------------------------
    message = (
        f"{emojis}{token} {interval}={price}{emojis}\n"
        f"{round(ratio, 2)} X     {hi_lo_label} = {low_price}\n"
        f"(Vmax1св) {int(vmax)} > {int(cep)} (Vсер.{count}св)\n"
        f"СПЛЕСК в {time_str}\n"
        f"{orders_block}"
    )

    return message
