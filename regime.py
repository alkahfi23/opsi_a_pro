# =====================================================
# OPSI A PRO — MARKET REGIME
# =====================================================
from indicators import accumulation_distribution

def detect_market_regime(df4h, df1d, score):
    price = df1d.close.iloc[-1]
    ema200 = df1d.close.ewm(span=200).mean().iloc[-1]
    adl = accumulation_distribution(df4h)

    structure = score["StructureScore"]
    volume = score["VolumeScore"]

    # =========================
    # CHOP / NO TRADE
    # =========================
    if structure < 40 and volume < 20:
        return "REGIME_CHOP"

    # =========================
    # MARKDOWN
    # =========================
    if price < ema200 and adl.iloc[-1] < adl.iloc[-20]:
        return "REGIME_MARKDOWN"

    # =========================
    # DISTRIBUTION
    # =========================
    if price > ema200 and adl.iloc[-1] < adl.iloc[-20]:
        return "REGIME_DISTRIBUTION"

    # =========================
    # MARKUP
    # =========================
    if price > ema200 and adl.iloc[-1] > adl.iloc[-20]:
        return "REGIME_MARKUP"

    # =========================
    # DEFAULT
    # =========================
    return "REGIME_ACCUMULATION"


def detect_regime_shift(df4h, df1d):
    adl = accumulation_distribution(df4h)
    ema200 = df1d.close.ewm(span=200).mean().iloc[-1]
    price = df1d.close.iloc[-1]

    if adl.iloc[-1] < adl.iloc[-30] and price < ema200:
        return {
            "Type": "SHIFT_TO_MARKDOWN",
            "Message": "⚠️ Distribution → Markdown (Institutional Exit)"
        }

    if adl.iloc[-1] > adl.iloc[-30] and price > ema200:
        return {
            "Type": "SHIFT_TO_MARKUP",
            "Message": "🚀 Accumulation → Markup (Institutional Entry)"
        }

    return None
