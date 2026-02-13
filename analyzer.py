"""
analyzer.py

Відповідає за:
- розрахунок середнього об'єму (CEP)
- пошук максимального об'єму (Vmax)
- обчислення коефіцієнта ratio = Vmax / CEP
- перевірку умови сплеску

НЕ використовує cep = 1
НЕ генерує сигнал якщо свічок < 55
"""

from config import K_SPIKE, MIN_CANDLES


def analyze(candles):
    if len(candles) < MIN_CANDLES:
        return None

    volumes = [float(c[5]) for c in candles]

    cep = sum(volumes) / len(volumes)

    vmax = max(volumes)

    ratio = vmax / cep

    if ratio < K_SPIKE:
        return None

    vmax_index = volumes.index(vmax)
    spike_candle = candles[vmax_index]

    return {
        "cep": cep,
        "vmax": vmax,
        "ratio": ratio,
        "spike_candle": spike_candle,
        "count": len(candles)
    }
