# =====================================================
# OPSI A PRO — SIGNAL ENGINE
# FUTURES WITH LTF ENTRY (PROP-FIRM GRADE, PATCHED)
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
from regime import detect_market_regime, detect_regime_shift
from risk import calculate_futures_position
from utils import now_wib, is_danger_time


# =====================================================
# LTF FUTURES ENTRY (EXECUTION ENGINE)
# =====================================================
def futures_ltf_entry(df_ltf, direction):
    """
    Return entry price or None

    Logic:
    - EMA20 reclaim / reject
    - Strong momentum confirmation
    """

    close = df_ltf.close
    ema20 = close.ewm(span=20).mean()

    if len(close) < 30:
        return None

    # LONG execution
    if direction == "LONG":
        if (
            close.iloc[-1] > ema20.iloc[-1] and
            close.iloc[-1] > close.iloc[-3]
        ):
            return close.iloc[-1]

    # SHORT execution
    if direction == "SHORT":
        if (
            close.iloc[-1] < ema20.iloc[-1] and
            close.iloc[-1] < close.iloc[-3]
        ):
            return close.iloc[-1]

    return None


# =====================================================
# MAIN SIGNAL CHECK
# =====================================================
def check_signal(symbol, mode, balance):
    """
    Return:
    - None
    - MARKET_WARNING
    - REGIME_SHIFT
    - TRADE_EXECUTION
    """

    # =========================
    # FUTURES KILL SWITCH
    # =========================
    if mode == "FUTURES" and is_danger_time():
        return None

    # =========================
    # FETCH DATA
    # =========================
    try:
        df4h = fetch_ohlcv(symbol, ENTRY_TF, LIMIT_4H)
        df1d = fetch_ohlcv(symbol, DAILY_TF, LIMIT_1D)
        df_ltf = fetch_ohlcv(symbol, LTF_TF, LIMIT_LTF)
    except Exception:
        return None

    if len(df4h) < 50 or len(df1d) < 50 or len(df_ltf) < 50:
        return None

    # =========================
    # HTF TREND
    # =========================
    _, trend = supertrend(df4h, period=10, mult=3.0)
    direction = "LONG" if trend.iloc[-1] == 1 else "SHORT"

    # =========================
    # INSTITUTIONAL SCORE
    # =========================
    score_data = institutional_score(df4h, df1d, direction)
    score = score_data["TotalScore"]

    if mode == "SPOT" and score < 70:
        return None
    if mode == "FUTURES" and score < 75:
        return None

    # =========================
    # MARKET REGIME
    # =========================
    regime = detect_market_regime(df4h, df1d, score_data)

    # =========================
    # REGIME SHIFT ALERT
    # =========================
    shift = detect_regime_shift(df4h, df1d)
    if shift:
        return {
            "SignalType": "REGIME_SHIFT",
            "Symbol": symbol,
            "Regime": regime,
            "Details": shift
        }

    # =========================
    # MODE PERMISSION
    # =========================
    if mode == "SPOT" and direction == "SHORT":
        return {
            "SignalType": "MARKET_WARNING",
            "Symbol": symbol,
            "Regime": regime,
            "Message": "SPOT short = distribution (no buy)"
        }

    if mode == "SPOT" and regime not in [
        "REGIME_ACCUMULATION",
        "REGIME_MARKUP"
    ]:
        return {
            "SignalType": "MARKET_WARNING",
            "Symbol": symbol,
            "Regime": regime,
            "Message": "No buy zone (institutional distribution)"
        }

    if mode == "FUTURES":
        if direction == "LONG" and regime not in [
            "REGIME_ACCUMULATION",
            "REGIME_MARKUP"
        ]:
            return None
        if direction == "SHORT" and regime not in [
            "REGIME_DISTRIBUTION",
            "REGIME_MARKDOWN"
        ]:
            return None

    # =========================
    # ADL CONFIRMATION (SOFT)
    # =========================
    adl = accumulation_distribution(df4h)

    if direction == "LONG" and adl.iloc[-1] <= adl.iloc[-20]:
        return None
    if direction == "SHORT" and adl.iloc[-1] >= adl.iloc[-20]:
        return None

    # =========================
    # ENTRY PRICE
    # =========================
    entry = df4h.close.iloc[-1]  # default (SPOT)

    if mode == "FUTURES":
        entry_ltf = futures_ltf_entry(df_ltf, direction)
        if not entry_ltf:
            return None

        # anti-chasing guard (max 1% from HTF price)
        htf_price = df4h.close.iloc[-1]
        if abs(entry_ltf - htf_price) / htf_price > 0.01:
            return None

        entry = entry_ltf

    # =========================
    # SL STRUCTURE (HTF)
    # =========================
    if direction == "LONG":
        supports = [
            s for s in find_support(df1d, SR_LOOKBACK)
            if s < entry
        ]
        if not supports:
            return None

        sl = max(supports) * (1 - ZONE_BUFFER)
        tp1 = entry + (entry - sl) * TP1_R
        tp2 = entry + (entry - sl) * TP2_R
        phase = "AKUMULASI_INSTITUSI"

    else:
        resistances = [
            r for r in find_resistance(df1d, SR_LOOKBACK)
            if r > entry
        ]
        if not resistances:
            return None

        sl = min(resistances) * (1 + ZONE_BUFFER)
        tp1 = entry - (sl - entry) * TP1_R
        tp2 = entry - (sl - entry) * TP2_R
        phase = "DISTRIBUSI_INSTITUSI"

    # =========================
    # FUTURES POSITION SIZE
    # =========================
    pos_size = 0.0
    if mode == "FUTURES":
        pos_size = calculate_futures_position(balance, entry, sl)

        if pos_size <= 0:
            return {
                "SignalType": "MARKET_WARNING",
                "Symbol": symbol,
                "Regime": regime,
                "Message": "Setup valid tapi SL masih terlalu lebar untuk futures"
            }

    # =========================
    # FINAL SIGNAL
    # =========================
    return {
        "SignalType": "TRADE_EXECUTION",
        "Time": now_wib(),
        "Symbol": symbol,
        "Phase": phase,
        "Regime": regime,
        "Score": score,
        "Entry": round(entry, 6),
        "SL": round(sl, 6),
        "TP1": round(tp1, 6),
        "TP2": round(tp2, 6),
        "Mode": mode,
        "Direction": direction,
        "PositionSize": pos_size
    }
