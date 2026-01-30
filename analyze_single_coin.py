# =====================================================
# OPSI A PRO — SINGLE COIN ANALYSIS (PATCHED)
# =====================================================

from config import (
    ENTRY_TF, DAILY_TF, LTF_TF,
    LIMIT_4H, LIMIT_1D, LIMIT_LTF,
    TP1_R, TP2_R, ZONE_BUFFER, SR_LOOKBACK
)

from exchange import fetch_ohlcv
from indicators import (
    supertrend,
    accumulation_distribution,
    find_support,
    find_resistance
)
from scoring import institutional_score
from regime import detect_market_regime
from risk import calculate_futures_position
from utils import is_danger_time


def analyze_single_coin(symbol, mode, balance):
    result = {
        "Symbol": symbol,
        "Trend": "NO TRADE",
        "Score": 0,
        "Entry": None,
        "SL": None,
        "TP1": None,
        "TP2": None,
        "PositionSize": None,
        "Reasons": []
    }

    # =========================
    # FUTURES KILL SWITCH
    # =========================
    if mode == "FUTURES" and is_danger_time():
        result["Reasons"].append("Danger time (futures disabled)")
        return result

    # =========================
    # FETCH DATA
    # =========================
    try:
        df4h = fetch_ohlcv(symbol, ENTRY_TF, LIMIT_4H)
        df1d = fetch_ohlcv(symbol, DAILY_TF, LIMIT_1D)
        df_ltf = fetch_ohlcv(symbol, LTF_TF, LIMIT_LTF)
    except Exception as e:
        result["Reasons"].append(f"Data error: {e}")
        return result

    if len(df4h) < 50 or len(df1d) < 50:
        result["Reasons"].append("Data tidak cukup")
        return result

    entry = df4h.close.iloc[-1]

    # =========================
    # DIRECTION
    # =========================
    _, trend = supertrend(df4h, period=10, mult=3.0)
    direction = "LONG" if trend.iloc[-1] == 1 else "SHORT"
    result["Trend"] = direction

    # =========================
    # SCORE
    # =========================
    score_data = institutional_score(df4h, df1d, direction)
    score = score_data["TotalScore"]
    result["Score"] = score

    if mode == "SPOT" and score < 70:
        result["Reasons"].append("Score < 70 (SPOT)")
        return result

    if mode == "FUTURES" and score < 75:
        result["Reasons"].append("Score < 75 (FUTURES)")
        return result

    # =========================
    # REGIME
    # =========================
    regime = detect_market_regime(df4h, df1d, score_data)

    if mode == "SPOT" and direction == "SHORT":
        result["Reasons"].append("SPOT short = distribution")
        return result

    # =========================
    # ADL CONFIRMATION (SOFT)
    # =========================
    adl = accumulation_distribution(df4h)

    if direction == "LONG" and adl.iloc[-1] <= adl.iloc[-20]:
        result["Reasons"].append("ADL belum akumulasi kuat")
        return result

    if direction == "SHORT" and adl.iloc[-1] >= adl.iloc[-20]:
        result["Reasons"].append("ADL belum distribusi kuat")
        return result

    # =========================
    # SL + TP
    # =========================
    if direction == "LONG":
        supports = [s for s in find_support(df1d, SR_LOOKBACK) if s < entry]
        if not supports:
            result["Reasons"].append("Tidak ada support valid")
            return result

        sl = max(supports) * (1 - ZONE_BUFFER)
        tp1 = entry + (entry - sl) * TP1_R
        tp2 = entry + (entry - sl) * TP2_R

    else:
        resistances = [r for r in find_resistance(df1d, SR_LOOKBACK) if r > entry]
        if not resistances:
            result["Reasons"].append("Tidak ada resistance valid")
            return result

        sl = min(resistances) * (1 + ZONE_BUFFER)
        tp1 = entry - (sl - entry) * TP1_R
        tp2 = entry - (sl - entry) * TP2_R

    # =========================
    # FUTURES POSITION SIZE (NO HARD KILL)
    # =========================
    pos_size = None
    if mode == "FUTURES":
        pos_size = calculate_futures_position(balance, entry, sl)

        if pos_size <= 0:
            stop_pct = abs(entry - sl) / entry
            result["Reasons"].append(
                f"SL terlalu jauh ({stop_pct*100:.2f}%) untuk futures"
            )
            # ⚠️ TIDAK return → tetap tampilkan struktur
    else:
        pos_size = 0

    # =========================
    # FINAL RESULT
    # =========================
    result.update({
        "Entry": round(entry, 6),
        "SL": round(sl, 6),
        "TP1": round(tp1, 6),
        "TP2": round(tp2, 6),
        "PositionSize": pos_size
    })

    if not result["Reasons"]:
        result["Trend"] = direction

    return result
