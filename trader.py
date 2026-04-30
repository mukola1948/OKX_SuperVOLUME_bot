# ================================================
# trader.py — OKX_Xay_Loy_bot
# Торгівля: виставлення ліміток і управління TP
#
# Логіка TP:
# Лім1 спрацювала (1 виконана) — вбудований TP від Лім1 (-5%)
# Лім2 спрацювала (2 виконані) — видаляємо TP від Лім1,
#   виставляємо TP(0.6) і TP(0.73) на оновлений об'єм
# Лім3-7 спрацювала — видаляємо ВСІ наявні TP (свої і ручні),
#   виставляємо нові TP(0.6) і TP(0.73) на оновлений об'єм
#
# Розподіл об'єму між двома TP:
#   TP(0.6) = ceil(об'єм_позиції * 2/3)
#   TP(0.73) = залишок
# ================================================
import math
from config import ORDER_UPDATE_THRESHOLD
from okx_client import (place_limit_order,
                         place_limit_order_with_tp,
                         cancel_order,
                         cancel_algo_order)

# Рівень Фібо для другого TP
FIBO_LEVEL_2 = 0.73


def _calc_fibo_73(current_high: float, next_low: float) -> float:
    """
    Розраховує рівень Фібо 0.73 — другий TP.
    Формула аналогічна Фібо 0.6:
    верхня точка мінус (верхня точка мінус нижня точка) * 0.73
    Верхня точка — найвищий Фх після Н.Лоя (поточний хай свінгу).
    Нижня точка — мінімум наступної свічки після Н.Лоя.
    """
    return round(current_high - (current_high - next_low) * FIBO_LEVEL_2, 4)


def _split_tp_volume(total_sz: int) -> tuple:
    """
    Розподіляє об'єм позиції між двома TP.
    TP(0.6) = ceil(total_sz * 2/3)
    TP(0.73) = залишок (total_sz - TP(0.6))
    Повертає (sz_06, sz_73).
    """
    sz_06 = math.ceil(total_sz * 2 / 3)
    sz_73 = total_sz - sz_06
    return sz_06, sz_73


def cancel_all_bot_orders(tp_algo_order_id: str,
                           open_orders: list) -> tuple:
    """
    Скасовує ВСІ активні ордери по інструменту при
    закритті позиції — і збережені ботом і змінені
    вручну. Це гарантує що жодна ліміта не залишиться
    висіти після закриття позиції.

    Алгоритм:
    1. Скасовуємо всі активні sell-ордери з біржі
       (ліміткі л1-л7, включаючи змінені вручну)
    2. Скасовуємо всі активні buy-ордери з reduceOnly
       (лімітні TP виставлені ботом або вручну)
    3. Скасовуємо алго-TP від л1 якщо є

    Повертає ([], "") — порожні ідентифікатори.
    """
    # Скасовуємо всі активні ордери з біржі по інструменту
    for o in open_orders:
        oid  = o.get("ordId", "")
        side = o.get("side", "")
        if not oid:
            continue
        try:
            cancel_order(oid)
            print(f"Скасовано {side}-ордер: {oid}")
        except Exception as e:
            print(f"Помилка скасування {oid}: {e}")

    # Скасовуємо алго-TP від л1 якщо ще активний
    if tp_algo_order_id:
        try:
            cancel_algo_order(tp_algo_order_id)
            print(f"Скасовано алго-TP: {tp_algo_order_id}")
        except Exception as e:
            print(f"Помилка скасування алго-TP: {e}")

    return [], ""


def cancel_all_tp_orders(tp_order_ids: list,
                          tp_algo_order_id: str,
                          open_orders: list,
                          algo_orders: list) -> tuple:
    """
    Скасовує всі наявні TP-ордери (і свої і ручні)
    без скасування лімітних ордерів бота.
    Використовується при спрацюванні Лім2+ для
    заміни TP на нові значення по Фібо.
    Повертає ([], "") — порожні ідентифікатори TP.

    Пояснення параметрів:
    tp_order_ids — список ідентифікаторів всіх TP
    tp_algo_order_id — ідентифікатор алго-TP від Лім1
    open_orders — активні лімітні ордери з біржі
    algo_orders — активні алго-ордери з біржі
    """
    open_ids    = {o["ordId"] for o in open_orders}
    algo_id_set = {o.get("algoId", "") for o in algo_orders}

    # Скасовуємо всі лімітні TP
    for tp_id in tp_order_ids:
        if tp_id and tp_id in open_ids:
            try:
                cancel_order(tp_id)
                print(f"Скасовано TP: {tp_id}")
            except Exception as e:
                print(f"Помилка скасування TP {tp_id}: {e}")

    # Скасовуємо алго-TP від Лім1 якщо ще активний
    if tp_algo_order_id and tp_algo_order_id in algo_id_set:
        try:
            cancel_algo_order(tp_algo_order_id)
            print(f"Скасовано алго-TP: {tp_algo_order_id}")
        except Exception as e:
            print(f"Помилка скасування алго-TP: {e}")

    return [], ""


def sync_bot_prices_from_exchange(bot_order_ids: list,
                                   open_orders: list) -> list:
    """
    Відновлює список цін ліміток з реальних
    активних ордерів на біржі.
    Якщо ордер виконаний (немає в активних) — ціна 0.0.

    Пояснення: це потрібно щоб бот бачив реальні
    ціни ліміток навіть якщо їх вручну змінили на біржі.
    """
    open_map = {o["ordId"]: float(o["px"])
                for o in open_orders}
    return [open_map.get(oid, 0.0) for oid in bot_order_ids]


def get_actual_tp_orders(tp_order_ids: list,
                          open_orders: list) -> list:
    """
    Повертає список активних TP-ордерів з біржі
    що відповідають збереженим ідентифікаторам TP.
    Включає ручні зміни — якщо ціна чи об'єм
    змінені вручну, повертає реальні значення з біржі.

    Пояснення: бот відстежує TP через ідентифікатори
    ордерів. Якщо користувач вручну змінив TP на біржі —
    ідентифікатор залишається тим самим але ціна і
    об'єм оновлюються. Ця функція повертає реальний стан.
    """
    open_map = {o["ordId"]: o for o in open_orders}
    result   = []
    for tp_id in tp_order_ids:
        if tp_id and tp_id in open_map:
            result.append(open_map[tp_id])
    return result


def sync_orders_with_levels(levels: list,
                             bot_order_ids: list,
                             bot_order_prices: list,
                             position,
                             open_orders: list) -> tuple:
    """
    Синхронізація лімітних ордерів з рівнями Фх.

    Кроки:
    1. Відновити ціни ліміток якщо список порожній
       але ідентифікатори є.
    2. Якщо є відкрита позиція — НЕ скидати і НЕ
       переставляти вже виставлені ліміткі. Додавати
       лише ті рівні які ще не покриті ордером.
       Також відстежувати ручні зміни цін ліміток.
    3. Якщо позиції немає і Лім1 змінилась > 0.3% —
       скидання всіх невиконаних ліміток і нове
       виставлення за поточними рівнями Фх.
    4. Лім1 виставляється з вбудованим TP (-5%).
       Лім2-7 — без вбудованого TP.

    Пояснення параметрів:
    levels — список рівнів Фх відібраних для ліміток
    bot_order_ids — збережені ідентифікатори ліміток
    bot_order_prices — збережені ціни ліміток
    position — дані відкритої позиції або None
    open_orders — активні ордери з біржі

    Повертає (bot_order_ids, bot_order_prices,
              new_order_ids, new_tp_price).
    new_order_ids — ідентифікатори виставлених в
    цьому запуску (для захисту від хибного плюса).
    new_tp_price — ціна вбудованого TP для Лім1
    якщо щойно виставили, інакше 0.0.
    """
    open_ids      = {o["ordId"]: o for o in open_orders}
    has_pos       = position is not None
    new_order_ids = []
    new_tp_price  = 0.0

    # Відновити ціни якщо порожні
    if bot_order_ids and not any(p > 0 for p in bot_order_prices):
        bot_order_prices = sync_bot_prices_from_exchange(
            bot_order_ids, open_orders
        )
        print(f"Відновлено ціни: {bot_order_prices}")

    # Виконані ордери: є в bot_order_ids, немає в активних,
    # є відкрита позиція
    filled_ids: set = set()
    if has_pos:
        filled_ids = {
            oid for oid in bot_order_ids
            if oid not in open_ids
        }

    new_ids    = list(bot_order_ids)
    new_prices = list(bot_order_prices)

    # Оновлюємо ціни з реальних ордерів
    # (враховуємо ручне переміщення на біржі)
    for i, oid in enumerate(new_ids):
        if oid in open_ids:
            real_price = float(open_ids[oid]["px"])
            if i < len(new_prices):
                new_prices[i] = real_price
            else:
                new_prices.append(real_price)

    if not levels:
        print("Рівні не знайдено — ліміткі не виставляються")
        return new_ids, new_prices, new_order_ids, new_tp_price

    # --- Якщо є відкрита позиція ---
    # Додаємо лише відсутні рівні, не чіпаємо існуючі
    if has_pos:
        covered_prices = set()
        for oid in new_ids:
            if oid in open_ids:
                covered_prices.add(
                    round(float(open_ids[oid]["px"]), 4)
                )

        for i, lvl in enumerate(levels):
            px = round(lvl["price"], 4)
            sz = lvl["sz"]

            # Слот вже виконаний — пропускаємо
            if i < len(new_ids) and new_ids[i] in filled_ids:
                continue

            # Рівень вже покритий активним ордером
            if any(abs(cp - px) / px * 100 < 0.1
                   for cp in covered_prices):
                continue

            try:
                if i == 0:
                    oid, tp_px = place_limit_order_with_tp(px, sz)
                    new_tp_price = tp_px
                else:
                    oid = place_limit_order("sell", px, sz)

                if i < len(new_ids):
                    new_ids[i]    = oid
                    new_prices[i] = px
                else:
                    new_ids.append(oid)
                    new_prices.append(px)
                covered_prices.add(px)
                new_order_ids.append(oid)
                print(f"Додано Лім{i + 1}: {px:.4f} sz={sz}")
            except Exception as e:
                print(f"Помилка Лім{i + 1}: {e}")

        return new_ids, new_prices, new_order_ids, new_tp_price

    # --- Якщо позиції немає ---
    # Перевіряємо чи потрібне скидання Лім1
    lim1_oid   = new_ids[0]    if new_ids    else None
    lim1_price = new_prices[0] if new_prices else None
    new_lim1   = round(levels[0]["price"], 4)

    lim1_active = (lim1_oid in open_ids) if lim1_oid else False

    need_reset = (
        lim1_active
        and lim1_price is not None
        and lim1_price > 0
        and abs(new_lim1 - lim1_price) / lim1_price
        > ORDER_UPDATE_THRESHOLD
    )

    if need_reset:
        print(
            f"Лім1 змінена {lim1_price:.4f}→{new_lim1:.4f}"
            f" → скидаємо"
        )
        for oid in new_ids:
            if oid in open_ids:
                try:
                    cancel_order(oid)
                    print(f"Скасовано при скиданні: {oid}")
                except Exception as e:
                    print(f"Помилка скасування: {e}")
        new_ids    = []
        new_prices = []

    # Виставляємо всі рівні що ще не покриті
    covered_prices = set()
    for oid in new_ids:
        if oid in open_ids:
            covered_prices.add(round(float(open_ids[oid]["px"]), 4))

    for i, lvl in enumerate(levels):
        px = round(lvl["price"], 4)
        sz = lvl["sz"]

        if any(abs(cp - px) / px * 100 < 0.1
               for cp in covered_prices):
            continue

        try:
            if i == 0:
                oid, tp_px = place_limit_order_with_tp(px, sz)
                new_tp_price = tp_px
            else:
                oid = place_limit_order("sell", px, sz)

            if i < len(new_ids):
                new_ids[i]    = oid
                new_prices[i] = px
            else:
                new_ids.append(oid)
                new_prices.append(px)
            covered_prices.add(px)
            new_order_ids.append(oid)
            print(f"Додано Лім{i + 1}: {px:.4f} sz={sz}")
        except Exception as e:
            print(f"Помилка Лім{i + 1}: {e}")

    return new_ids, new_prices, new_order_ids, new_tp_price


def check_and_update_tp(position,
                         fibo_06: float,
                         fibo_73: float,
                         current_high: float,
                         tp_order_ids: list,
                         tp_algo_order_id: str,
                         last_fibo_high: float,
                         filled_count: int,
                         open_orders: list,
                         algo_orders: list,
                         state: dict) -> tuple:
    """
    Управління TP залежно від кількості виконаних ліміток.

    filled_count = 0: позиції немає — нічого не робимо.
    filled_count = 1: Лім1 спрацювала — TP керується
      вбудованим алго-ордером від Лім1, не чіпаємо.
    filled_count = 2 (саме Лім2 щойно спрацювала):
      — видаляємо TP від Лім1 (алго-TP)
      — виставляємо TP(0.6) і TP(0.73) на оновлений об'єм
    filled_count >= 3 (Лім3-7 щойно спрацювала):
      — видаляємо ВСІ наявні TP (і свої і ручні)
      — виставляємо нові TP(0.6) і TP(0.73)

    Якщо TP вже виставлені і хай свінгу не змінився —
    не чіпаємо (навіть якщо користувач змінив вручну).

    Пояснення параметрів:
    position — дані відкритої позиції або None
    fibo_06 — ціна рівня Фібо 0.6 (перший TP)
    fibo_73 — ціна рівня Фібо 0.73 (другий TP)
    current_high — поточний найвищий хай свінгу після Н.Лоя
    tp_order_ids — список ідентифікаторів поточних TP
    tp_algo_order_id — ідентифікатор вбудованого алго-TP
    last_fibo_high — хай свінгу при попередньому розрахунку
    filled_count — кількість виконаних ліміток
    open_orders — активні ордери з біржі
    algo_orders — активні алго-ордери з біржі
    state — поточний стан бота

    Повертає (tp_order_ids, tp_algo_order_id,
              tp_price_06, tp_price_73, last_fibo_high).
    """
    tp_price_06 = state.get("tp_price_06", 0.0)
    tp_price_73 = state.get("tp_price_73", 0.0)

    if position is None:
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    pos_sz   = abs(int(float(position.get("pos", 0))))
    open_ids = {o["ordId"] for o in open_orders}

    # filled_count = 1: тільки Лім1 — не чіпаємо алго-TP
    if filled_count < 2:
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    # Перевіряємо чи Фібо вигідні (нижче середньої ціни входу)
    avg_px = float(position.get("avgPx", 0))
    if not fibo_06 or fibo_06 >= avg_px:
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    # Перевіряємо чи хай свінгу змінився
    high_changed = current_high > last_fibo_high > 0

    # Чи є вже активні TP-ордери на біржі
    active_tp_count = sum(
        1 for tp_id in tp_order_ids
        if tp_id and tp_id in open_ids
    )

    # Якщо filled_count == 2 і TP вже виставлені і хай не змінився
    # — не чіпаємо (користувач міг змінити вручну)
    if filled_count == 2 and active_tp_count >= 1 and not high_changed:
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    # Якщо filled_count >= 3 і хай не змінився і TP є — не чіпаємо
    # (перевіряємо чи це та сама кількість виконаних що була)
    prev_filled = state.get("prev_filled_count", 0)
    if (filled_count >= 3
            and filled_count == prev_filled
            and active_tp_count >= 1
            and not high_changed):
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    # --- Потрібно оновити TP ---
    # Скасовуємо всі наявні TP
    new_tp_ids, new_algo_id = cancel_all_tp_orders(
        tp_order_ids, tp_algo_order_id, open_orders, algo_orders
    )

    # Розподіляємо об'єм між двома TP
    sz_06, sz_73 = _split_tp_volume(pos_sz)

    # Виставляємо TP(0.6)
    try:
        oid_06      = place_limit_order("buy", fibo_06, sz_06,
                                         reduce_only=True)
        new_tp_ids  = [oid_06]
        tp_price_06 = fibo_06
        print(f"TP(0.6): {fibo_06:.4f} sz={sz_06}")
    except Exception as e:
        print(f"Помилка виставлення TP(0.6): {e}")
        return (tp_order_ids, tp_algo_order_id,
                tp_price_06, tp_price_73, last_fibo_high)

    # Виставляємо TP(0.73) якщо об'єм більше 0
    if sz_73 > 0:
        try:
            oid_73      = place_limit_order("buy", fibo_73, sz_73,
                                             reduce_only=True)
            new_tp_ids.append(oid_73)
            tp_price_73 = fibo_73
            print(f"TP(0.73): {fibo_73:.4f} sz={sz_73}")
        except Exception as e:
            print(f"Помилка виставлення TP(0.73): {e}")

    return (new_tp_ids, new_algo_id,
            tp_price_06, tp_price_73, current_high)
