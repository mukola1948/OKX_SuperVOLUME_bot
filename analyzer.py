"""
analyzer.py

Логіка:
- аналізуються лише нові свічки (відфільтровані в main.py)
- спочатку визначається Vmax серед нових свічок
- CEP рахується лише по тих нових свічках,
  обʼєм яких <= Vmax / 2
- потім визначаються свічки-сплески (>= K_SPIKE * CEP)
- використовується тільки одна — з найбільшим volume
"""

from config import K_SPIKE


def analyze(candles):

    # Якщо нових свічок немає — вихід
    if not candles:
        return None

    # 1️⃣ Визначаємо Vmax серед нових свічок
    volumes = [float(c[5]) for c in candles]
    vmax_global = max(volumes)

    # 2️⃣ Формуємо масив для CEP:
    #    тільки ті свічки, що <= Vmax / 1.8
    cep_volumes = [v for v in volumes if v <= (vmax_global / 2)]

    if not cep_volumes:
        return None

    cep = sum(cep_volumes) / len(cep_volumes)

    spike_candidates = []

    # 3️⃣ Пошук свічок зі сплеском
    for candle in candles:
        volume = float(candle[5])
        ratio = volume / cep if cep > 0 else 0

        if ratio >= K_SPIKE:
            spike_candidates.append((candle, volume, ratio))

    if not spike_candidates:
        return None

    # 4️⃣ Вибираємо одну — з найбільшим volume
    spike_candidates.sort(key=lambda x: x[1], reverse=True)
    best_candle, best_volume, best_ratio = spike_candidates[0]

    return {
        "candle": best_candle,
        "vmax": best_volume,
        "ratio": best_ratio,
        "cep": cep,
        "spike_count": len(spike_candidates),
        "analyzed_candles": len(candles),
    }
