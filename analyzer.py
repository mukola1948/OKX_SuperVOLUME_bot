"""
analyzer.py

Логіка:
- розрахунок CEP
- перевірка кожної свічки
- повернення списку сплесків
"""

from config import K_SPIKE, MIN_CANDLES


def analyze(candles):
    if len(candles) < MIN_CANDLES:
        return []

    volumes = [float(c[5]) for c in candles]
    cep = sum(volumes) / len(volumes)

    spikes = []

    for i, candle in enumerate(candles):
        volume = float(candle[5])
        ratio = volume / cep

        if ratio >= K_SPIKE:
            spikes.append({
                "candle": candle,
                "ratio": ratio,
                "volume": volume,
                "cep": cep,
                "index": i
            })

    return spikes
