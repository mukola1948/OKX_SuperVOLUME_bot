# ============================================================
# ФАЙЛ: analyzer.py
# Опис:
# Уся МАТЕМАТИКА: Vmax, CEP, ratio, spike_price
# ============================================================

def analyze(candles, cep_old):
    volumes = []
    colors = []
    lows = []
    highs = []

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

    vmax = max(volumes)
    vmax_index = volumes.index(vmax)

    filtered = [v for v in volumes if v < vmax / 2]
    cep_new = sum(filtered) / len(filtered) if filtered else cep_old

    ratio = vmax / cep_old if cep_old else 0
    spike_price = highs[vmax_index] if colors[vmax_index] else lows[vmax_index]

    return {
        "vmax": vmax,
        "cep_new": cep_new,
        "ratio": ratio,
        "is_green": colors[vmax_index],
        "vmax_count": 1,
        "cep_count": len(filtered),
        "spike_price": spike_price,
    }
