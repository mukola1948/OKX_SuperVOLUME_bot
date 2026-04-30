# ================================================
# fractals.py — OKX_Xay_Loy_bot
# Завантаження і збереження історії Фх і Фл.
# Файли: fractal_hay.json і fractal_loy.json
#
# Формат запису Фх: "ДД.ММ.РР ГГ:ХХ;ts;ціна;tf"
# Формат запису Фл: "ДД.ММ.РР ГГ:ХХ;ts;ціна;
#                    next_low;cross_count;tf"
# Роздільник ; для зручного імпорту в Excel.
# ================================================
import json
import os
from datetime import datetime, timezone
from config import FRACTAL_WINDOW, FIBO_LEVEL

HAY_FILE = "fractal_hay.json"
LOY_FILE = "fractal_loy.json"


# -----------------------------------------------
# Допоміжні функції перетворення часу
# -----------------------------------------------
def _ts_to_datetime(ts_ms: int) -> str:
    """Позначка часу мс → рядок 'ДД.ММ.РР ГГ:ХХ' UTC"""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%d.%m.%y %H:%M")


def _ts_to_date(ts_ms: int) -> str:
    """Позначка часу мс → рядок 'ДД.ММ.РР' UTC"""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%d.%m.%y")


# -----------------------------------------------
# Конвертація між рядковим форматом і словником
# -----------------------------------------------
def _hay_to_str(h: dict) -> str:
    tf = h.get("tf", "5m")
    return f"{h['date']};{h['ts']};{h['price']};{tf}"


def _loy_to_str(lw: dict) -> str:
    tf = lw.get("tf", "5m")
    return (f"{lw['date']};{lw['ts']};{lw['price']};"
            f"{lw['next_low']};{lw['cross_count']};{tf}")


def _str_to_hay(s: str) -> dict:
    parts = s.split(";")
    if len(parts) < 4:
        raise ValueError(f"Невірний формат Фх: {s}")
    return {
        "date":  parts[0],
        "ts":    int(parts[1]),
        "price": float(parts[2]),
        "tf":    parts[3],
    }


def _str_to_loy(s: str) -> dict:
    parts = s.split(";")
    if len(parts) < 6:
        raise ValueError(f"Невірний формат Фл: {s}")
    return {
        "date":        parts[0],
        "ts":          int(parts[1]),
        "price":       float(parts[2]),
        "next_low":    float(parts[3]),
        "cross_count": int(parts[4]),
        "tf":          parts[5],
    }


# -----------------------------------------------
# Завантаження файлів Фх і Фл
# -----------------------------------------------
def load_fractals() -> tuple:
    """
    Завантажує fractal_hay.json і fractal_loy.json.
    Кожен файл — стандартний JSON де поле items
    містить список рядків формату з роздільником ;
    Якщо файл не існує — повертає порожню структуру.
    Повертає (hay_data, loy_data) де items — list[dict].
    """
    def _load_hay(path):
        if not os.path.exists(path):
            return {
                "description": "Фх. Формат: дата час;ts;ціна;tf",
                "last_updated": "",
                "items": [],
            }
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = []
        for item in raw.get("items", []):
            if isinstance(item, str):
                try:
                    items.append(_str_to_hay(item))
                except (ValueError, IndexError):
                    print(f"Пропущено невалідний Фх: {item}")
            elif isinstance(item, dict):
                items.append(item)
        raw["items"] = items
        return raw

    def _load_loy(path):
        if not os.path.exists(path):
            return {
                "description": (
                    "Фл. Формат: дата час;ts;ціна;"
                    "next_low;cross_count;tf"
                ),
                "last_updated": "",
                "items": [],
            }
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = []
        for item in raw.get("items", []):
            if isinstance(item, str):
                try:
                    items.append(_str_to_loy(item))
                except (ValueError, IndexError):
                    print(f"Пропущено невалідний Фл: {item}")
            elif isinstance(item, dict):
                items.append(item)
        raw["items"] = items
        return raw

    return _load_hay(HAY_FILE), _load_loy(LOY_FILE)


def save_fractals(hay_data: dict, loy_data: dict):
    """
    Зберігає Фх і Фл у валідному JSON форматі.
    Кожен запис — рядок з роздільником ; для Excel.
    """
    now = _ts_to_datetime(
        int(datetime.now(timezone.utc).timestamp() * 1000)
    )
    hay_out = {
        "description":  hay_data.get(
            "description", "Фх. Формат: дата час;ts;ціна;tf"
        ),
        "last_updated": now,
        "items": [_hay_to_str(h) for h in hay_data["items"]],
    }
    with open(HAY_FILE, "w", encoding="utf-8") as f:
        json.dump(hay_out, f, ensure_ascii=False, indent=2)

    loy_out = {
        "description":  loy_data.get(
            "description",
            "Фл. Формат: дата час;ts;ціна;next_low;cross_count;tf"
        ),
        "last_updated": now,
        "items": [_loy_to_str(lw) for lw in loy_data["items"]],
    }
    with open(LOY_FILE, "w", encoding="utf-8") as f:
        json.dump(loy_out, f, ensure_ascii=False, indent=2)


# -----------------------------------------------
# Пошук нових Фх і Фл у пакеті свічок
# -----------------------------------------------
def find_new_fractals(candles: list,
                       existing_hay_ts: set,
                       existing_loy_ts: set,
                       tf: str,
                       window: int = FRACTAL_WINDOW) -> tuple:
    """
    Шукає нові фрактальні хаї і фрактальні лої
    у списку свічок.
    tf — таймфрейм пакету ('5m' або '15m').
    Пропускає ті що вже є в існуючих множинах
    позначок часу.
    Повертає (new_hay_items, new_loy_items).
    """
    n       = len(candles)
    new_hay = []
    new_loy = []

    for i in range(window, n - window):
        ts     = int(candles[i][0])
        dt_str = _ts_to_datetime(ts)

        # Фрактальний хай
        high_i  = float(candles[i][2])
        left_h  = [float(candles[i - j][2])
                   for j in range(1, window + 1)]
        right_h = [float(candles[i + j][2])
                   for j in range(1, window + 1)]
        if (high_i > max(left_h)
                and high_i > max(right_h)
                and ts not in existing_hay_ts):
            new_hay.append({
                "date":  dt_str,
                "ts":    ts,
                "price": round(high_i, 4),
                "tf":    tf,
            })

        # Фрактальний лой
        low_i   = float(candles[i][3])
        left_l  = [float(candles[i - j][3])
                   for j in range(1, window + 1)]
        right_l = [float(candles[i + j][3])
                   for j in range(1, window + 1)]
        if (low_i < min(left_l)
                and low_i < min(right_l)
                and ts not in existing_loy_ts):
            next_low = float(candles[i + 1][3])
            new_loy.append({
                "date":        dt_str,
                "ts":          ts,
                "price":       round(low_i, 4),
                "next_low":    round(next_low, 4),
                "cross_count": 0,
                "tf":          tf,
            })

    return new_hay, new_loy


# -----------------------------------------------
# Очищення перекритих Фх
# -----------------------------------------------
def clean_hay(hay_items: list) -> list:
    """
    Очищає список Фх згідно правила:
    всі значення Фх від найновішого до найстарішого
    повинні тільки зростати.
    Тобто якщо Фх[i] (новіший) >= Фх[j] (старіший)
    — Фх[j] перекритий і видаляється.
    Алгоритм: від найновішого до найстарішого,
    зберігаємо поточний максимум. Якщо Фх нижчий
    або рівний поточному максимуму — він перекритий
    і видаляється. Якщо вищий — оновлюємо максимум
    і зберігаємо.
    """
    # Сортуємо від нових (великий ts) до старих
    sorted_hay = sorted(hay_items, key=lambda x: x["ts"], reverse=True)
    result      = []
    running_max = 0.0

    for h in sorted_hay:
        if h["price"] > running_max:
            running_max = h["price"]
            result.append(h)
        # Якщо h["price"] <= running_max — Фх перекритий,
        # не додаємо до результату

    # Повертаємо відсортованими від нових до старих
    return result


# -----------------------------------------------
# Оновлення лічильника перекриттів Фл
# ВИПРАВЛЕНО: між двома перекриттями обов'язково
# мають бути вищі Фл (відскок вгору між пробоями)
# -----------------------------------------------
def update_loy_cross_count(loy_items: list) -> list:
    """
    Оновлює лічильник перекриттів (cross_count)
    для кожного Фл в єдиному загальному списку
    (незалежно від таймфрейму 5m чи 15m).

    Правило подвійного перекриття:
    Перше перекриття — з'явився новіший Фл нижчий
    за даний. cross_count = 1, Фл залишається.
    Між першим і другим перекриттям обов'язково
    мають бути новіші Фл ВИЩІ за даний Фл
    (відскок вгору — ціна повернулась вище).
    Друге перекриття — знову з'явився новіший Фл
    нижчий за даний після відскоку. cross_count = 2,
    Фл видаляється з списку.

    Алгоритм (від старих до нових):
    Для кожного Фл[i] проходимо по новіших Фл[j]:
    1. Шукаємо перший новіший Фл нижчий за Фл[i]
       → це перше перекриття
    2. Після першого перекриття шукаємо новіший Фл
       ВИЩИЙ за Фл[i] → це підтвердження відскоку
    3. Після відскоку шукаємо ще один новіший Фл
       нижчий за Фл[i] → це друге перекриття
    Якщо знайдені всі 3 кроки → cross_count = 2
    Якщо знайдені кроки 1 (і не 2,3) → cross_count = 1
    Якщо крок 1 не знайдено → cross_count = 0
    """
    # Сортуємо від старих (малий ts) до нових
    sorted_loy = sorted(loy_items, key=lambda x: x["ts"])
    n = len(sorted_loy)

    for i, fl in enumerate(sorted_loy):
        price_i = fl["price"]
        count   = 0

        # Стан машини: 0=шукаємо перше перекриття,
        # 1=шукаємо відскок, 2=шукаємо друге перекриття
        stage = 0

        for j in range(i + 1, n):
            price_j = sorted_loy[j]["price"]

            if stage == 0:
                # Шукаємо перший новіший Фл нижчий за fl
                if price_j < price_i:
                    count = 1
                    stage = 1

            elif stage == 1:
                # Шукаємо відскок вгору — Фл вищий за fl
                if price_j > price_i:
                    stage = 2

            elif stage == 2:
                # Шукаємо друге перекриття — Фл нижчий за fl
                if price_j < price_i:
                    count = 2
                    break  # Двічі перекритий — зупиняємось

        fl["cross_count"] = count

    # Видаляємо двічі перекриті (cross_count >= 2)
    result = [fl for fl in sorted_loy if fl["cross_count"] < 2]
    # Повертаємо від нових до старих
    result.sort(key=lambda x: x["ts"], reverse=True)
    return result


# -----------------------------------------------
# Оновлення списків Фх і Фл з пакету свічок
# -----------------------------------------------
def update_fractals_from_candles(candles: list,
                                  hay_data: dict,
                                  loy_data: dict,
                                  tf: str,
                                  is_new: bool = True) -> tuple:
    """
    Знаходить нові Фх і Фл в пакеті свічок
    і додає їх до відповідних списків.
    is_new=True  — нові свічки між запусками:
                   додаємо на початок (нові до нових)
    is_new=False — стара (глибинна) історія:
                   додаємо в кінець (старі до старих)
    Після додавання очищує перекриті Фх і
    оновлює лічильники перекриттів Фл.
    """
    existing_hay_ts = {h["ts"] for h in hay_data["items"]}
    existing_loy_ts = {lw["ts"] for lw in loy_data["items"]}

    new_hay, new_loy = find_new_fractals(
        candles, existing_hay_ts, existing_loy_ts, tf
    )

    if new_hay:
        if is_new:
            hay_data["items"] = new_hay + hay_data["items"]
        else:
            hay_data["items"] = hay_data["items"] + new_hay

    if new_loy:
        if is_new:
            loy_data["items"] = new_loy + loy_data["items"]
        else:
            loy_data["items"] = loy_data["items"] + new_loy

    # Сортуємо від нових до старих
    hay_data["items"].sort(key=lambda x: x["ts"], reverse=True)
    loy_data["items"].sort(key=lambda x: x["ts"], reverse=True)

    # Очищення перекритих Фх
    hay_data["items"] = clean_hay(hay_data["items"])

    # Оновлення лічильників і видалення двічі перекритих Фл
    loy_data["items"] = update_loy_cross_count(loy_data["items"])

    return hay_data, loy_data


# -----------------------------------------------
# Застосування правил очищення без нових свічок
# Викликається при кожному запуску щоб гарантувати
# що перекриті Фх видалені навіть якщо нових свічок
# не було (менше 5 свічок між запусками)
# -----------------------------------------------
def apply_fractal_rules(hay_data: dict,
                        loy_data: dict) -> tuple:
    """
    Застосовує правила очищення Фх і Фл без пошуку
    нових фракталів. Сортує, очищає перекриті Фх,
    оновлює лічильники перекриттів Фл.
    Викликається при кожному запуску незалежно від
    кількості нових свічок.
    """
    hay_data["items"].sort(key=lambda x: x["ts"], reverse=True)
    loy_data["items"].sort(key=lambda x: x["ts"], reverse=True)
    hay_data["items"] = clean_hay(hay_data["items"])
    loy_data["items"] = update_loy_cross_count(loy_data["items"])
    return hay_data, loy_data


# -----------------------------------------------
# Отримання граничних дат для рядку Історія
# -----------------------------------------------
def get_fractal_date_range(data: dict, tf: str) -> tuple:
    """
    Повертає (найновіша_дата, найстаріша_дата) для
    Фх або Фл вказаного таймфрейму tf.
    Дата — лише ДД.ММ.РР (без часу) для повідомлення.
    Якщо немає жодного запису — повертає ("", "").
    """
    items = [
        item for item in data.get("items", [])
        if item.get("tf") == tf
    ]
    if not items:
        return "", ""
    newest = max(items, key=lambda x: x["ts"])
    oldest = min(items, key=lambda x: x["ts"])
    newest_date = newest["date"].split(" ")[0]
    oldest_date = oldest["date"].split(" ")[0]
    return newest_date, oldest_date


# -----------------------------------------------
# Пошук ОЛЛ (останній локальний лой)
# Логіка: беремо 12 найближчих Фл нижче поточної
# ціни відсортованих від нових до старих і
# вибираємо серед них мінімальний.
# Без груп, без складної логіки розвороту.
# -----------------------------------------------
def find_current_low(loy_data: dict,
                     current_price: float = 0.0) -> dict:
    """
    Знаходить ОЛЛ (останній локальний лой) —
    мінімум серед 12 найближчих Фл нижче поточної ціни.

    Алгоритм:
    1. Фільтруємо — лише Фл нижче поточної ціни
    2. Сортуємо від нових до старих
    3. Беремо перші 12 (найближчі до поточного моменту)
    4. З них вибираємо той що має найнижчу ціну — це ОЛЛ

    Якщо current_price = 0.0 — фільтрація не застосовується.
    Повертає {date, ts, price, next_low} або {}.
    """
    items = loy_data.get("items", [])
    if not items:
        return {}

    # Фільтруємо: лише Фл нижче поточної ціни
    if current_price > 0.0:
        filtered = [fl for fl in items if fl["price"] < current_price]
    else:
        filtered = list(items)

    if not filtered:
        return {}

    # Сортуємо від нових до старих, беремо 12 найближчих
    sorted_items = sorted(filtered, key=lambda x: x["ts"], reverse=True)
    candidates   = sorted_items[:12]

    if not candidates:
        return {}

    # ОЛЛ — мінімальний серед 12 найближчих
    oll = min(candidates, key=lambda x: x["price"])
    return {
        "date":     oll["date"],
        "ts":       oll["ts"],
        "price":    oll["price"],
        "next_low": oll["next_low"],
    }


# -----------------------------------------------
# Розрахунок Фібо 0.6
# -----------------------------------------------
def calc_fibo_06(candles: list,
                 current_low: dict,
                 hay_data: dict) -> tuple:
    """
    Розраховує рівень Фібо 0.6 від поточного Н.Лоя.

    Нижня точка сітки (Фібо 1.0) = next_low
    (мінімум наступної свічки після Н.Лоя).
    Верхня точка сітки (Фібо 0.0) = найвищий Фх
    після Н.Лоя або поточний максимум свічок.

    Формула: Фібо 0.6 = верхня точка мінус
    (верхня точка мінус нижня точка) * 0.6

    Повертає (fibo_06, current_high).
    Якщо даних недостатньо — повертає (None, 0.0).
    """
    if not current_low:
        return None, 0.0

    low_ts   = current_low.get("ts", 0)
    next_low = current_low.get("next_low", 0.0)

    if not low_ts or not next_low:
        return None, 0.0

    # Фх після Н.Лоя
    after_low = [
        h for h in hay_data.get("items", [])
        if h["ts"] > low_ts
    ]

    # Поточний максимум з останніх свічок
    if candles:
        recent  = candles[-(FRACTAL_WINDOW + 1):]
        cur_max = max(float(c[2]) for c in recent)
        cur_ts  = int(candles[-1][0])
        if cur_ts > low_ts:
            after_low.append({"ts": cur_ts, "price": cur_max})

    if not after_low:
        return None, 0.0

    current_high = max(h["price"] for h in after_low)
    fibo_06      = round(
        current_high - (current_high - next_low) * FIBO_LEVEL, 4
    )
    return fibo_06, current_high
