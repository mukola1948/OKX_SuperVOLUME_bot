"""
analyzer.py

Логіка:
- аналізуються лише нові свічки (відфільтровані в main.py)
- CEP рахується тільки по цих свічках
- знаходимо всі свічки зі сплеском
- вибираємо одну з максимальним VOLUME
"""

from config import K_SPIKE


def analyze(candles):

    # Якщо нових свічок немає — вихід
    if not candles:
        return None

    # Розрахунок CEP тільки по нових свічках
    volumes = [float(c[5]) for c in candles]
    cep = sum(volumes) / len(volumes)

    spike_candidates = []

    # Пошук свічок зі сплеском
    for candle in candles:
        volume = float(candle[5])
        ratio = volume / cep if cep > 0 else 0

        if ratio >= K_SPIKE:
            spike_candidates.append((candle, volume, ratio))

    if not spike_candidates:
        return None

    # Вибираємо одну — з найбільшим volume
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
