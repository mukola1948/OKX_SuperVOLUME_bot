"""
analyzer.py

Логіка:
- рахуємо CEP по фактично переданих свічках
- знаходимо всі свічки зі сплеском
- вибираємо одну з максимальним VOLUME
- повертаємо реальну кількість свічок для відображення
"""

from config import K_SPIKE, MIN_CANDLES


def analyze(candles):

    # Перевірка мінімальної кількості свічок
    if len(candles) < MIN_CANDLES:
        return None

    # Розрахунок CEP
    volumes = [float(c[5]) for c in candles]
    cep = sum(volumes) / len(volumes)

    spike_candidates = []

    # Пошук свічок зі сплеском
    for candle in candles:
        volume = float(candle[5])
        ratio = volume / cep

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
        "analyzed_candles": len(candles),  # ← РЕАЛЬНА кількість
    }
