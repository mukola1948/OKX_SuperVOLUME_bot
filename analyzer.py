"""
analyzer.py

Логіка:
- рахуємо CEP
- знаходимо всі свічки зі сплеском
- вибираємо одну з максимальним VOLUME
"""

from config import K_SPIKE, MIN_CANDLES


def analyze(candles):

    if len(candles) < MIN_CANDLES:
        return None

    volumes = [float(c[5]) for c in candles]
    cep = sum(volumes) / len(volumes)

    spike_candidates = []

    for candle in candles:
        volume = float(candle[5])
        ratio = volume / cep

        if ratio >= K_SPIKE:
            spike_candidates.append((candle, volume, ratio))

    if not spike_candidates:
        return None

    # вибираємо тільки один — з найбільшим volume
    spike_candidates.sort(key=lambda x: x[1], reverse=True)
    best_candle, best_volume, best_ratio = spike_candidates[0]

    return {
        "candle": best_candle,
        "vmax": best_volume,
        "ratio": best_ratio,
        "cep": cep,
        "spike_count": len(spike_candidates)
    }
