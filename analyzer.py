# ============================================================
# ФАЙЛ: analyzer.py
# Опис:
# Розрахунок vmax, CEP та ratio БЕЗ fallback значень
# ============================================================

def analyze(candles):
    volumes = []
    lows = []
    highs = []
    colors = []

    for c in candles:
        open_p = float(c[1])
        high_p = float(c[2])
        low_p = float(c[3])
        close_p = float(c[4])
        volume = float(c[5])

        volumes.append(volume)
        lows.append(low_p)
        highs.append(high_p)
        colors.append(close_p >= open_p)

    if not volumes:
        return None

    vmax = max(volumes)
    vmax_index = volumes.index(vmax)

    # CEP = середнє всіх обʼємів менших за vmax
    filtered = [v for v in volumes if v < vmax]

    if not filtered:
        return None  # якщо нема бази для порівняння — сигнал не формуємо

    cep = sum(filtered) / len(filtered)
    ratio = vmax / cep

    spike_price = highs[vmax_index] if colors[vmax_index] else lows[vmax_index]

    return {
        "vmax": vmax,
        "cep": cep,
        "ratio": ratio,
        "is_green": colors[vmax_index],
        "vmax_index": vmax_index,
        "spike_price": spike_price,
    }
