# =====================================================
# OPSI A PRO — INSTITUTIONAL SCORING
# =====================================================
from indicators import volume_osc, accumulation_distribution

def institutional_score(df4h, df1d, direction="LONG"):
    price = df4h.close.iloc[-1]

    ema20 = df4h.close.ewm(span=20).mean().iloc[-1]
    ema50 = df4h.close.ewm(span=50).mean().iloc[-1]
    ema200 = df1d.close.ewm(span=200).mean().iloc[-1]

    # =========================
    # 1. STRUCTURE (40)
    # =========================
    structure = 0
    if direction == "LONG":
        if price > ema20: structure += 15
        if ema20 > ema50: structure += 10
        if ema50 > ema200: structure += 10
        if price > ema200: structure += 5
    else:
        if price < ema20: structure += 15
        if ema20 < ema50: structure += 10
        if ema50 < ema200: structure += 10
        if price < ema200: structure += 5

    structure = min(structure, 40)

    # =========================
    # 2. VOLUME (30)
    # =========================
    vo = volume_osc(df4h.volume).iloc[-1]
    volume = 0
    if vo > 3: volume += 10
    if vo > 10: volume += 10
    if vo > 20: volume += 10
    volume = min(volume, 30)

    # =========================
    # 3. ADL FLOW (30)
    # =========================
    adl = accumulation_distribution(df4h)
    adl_score = 0

    if direction == "LONG":
        if adl.iloc[-1] > adl.iloc[-5]: adl_score += 10
        if adl.iloc[-1] > adl.iloc[-10]: adl_score += 10
        if adl.iloc[-1] > adl.iloc[-20]: adl_score += 10
    else:
        if adl.iloc[-1] < adl.iloc[-5]: adl_score += 10
        if adl.iloc[-1] < adl.iloc[-10]: adl_score += 10
        if adl.iloc[-1] < adl.iloc[-20]: adl_score += 10

    adl_score = min(adl_score, 30)

    return {
        "TotalScore": structure + volume + adl_score,
        "StructureScore": structure,
        "VolumeScore": volume,
        "ADLScore": adl_score
    }
