# =====================================================
# OPSI A PRO — SIGNAL ENGINE
# =====================================================
from config import (
    ENTRY_TF, DAILY_TF, LTF_TF,
    LIMIT_4H, LIMIT_1D, LIMIT_LTF,
    TP1_R, TP2_R, ZONE_BUFFER, SR_LOOKBACK
)
from exchange import fetch_ohlcv
from indicators import supertrend, accumulation_distribution, find_support, find_resistance
from scoring import institutional_score
from regime import detect_market_regime, detect_regime_shift
from risk import calculate_futures_position
from utils import now_wib, is_danger_time

def execution_confirmation(df_ltf, direction):
    close = df_ltf.close
    ema20 = close.ewm(span=20).mean()

    if direction == "LONG":
        if close.iloc[-1] < ema20.iloc[-1]:
            return False
        if close.iloc[-1] < close.iloc[-3]:
            return False

    if direction == "SHORT":
        if close.iloc[-1] > ema20.iloc[-1]:
            return False
        if close.iloc[-1] > close.iloc[-3]:
            return False

    return True


def check_signal(okx, symbol, mode, balance):
    # =========================
    # Futures kill-switch
    # =========================
    if mode == "FUTURES" and is_danger_time():
        return None

    # =========================
    # Fetch data
    # =========================
    df4h = fetch_ohlcv(okx, symbol, ENTRY_TF, LIMIT_4H)
    df1d = fetch_ohlcv(okx, symbol, DAILY_TF, LIMIT_1D)
    df_ltf = fetch_ohlcv(okx, symbol, LTF_TF, LIMIT_LTF)

    entry = df4h.close.iloc[-1]

    # =========================
    # Direction
    # =========================
    _, trend = supertrend(df4h, period=10, mult=3.0)
    direction = "LONG" if trend.iloc[-1] == 1 else "SHORT"

    # =========================
    # Institutional Score
    # =========================
    score_data = institutional_score(df4h, df1d, direction)
    score = score_data["TotalScore"]

    if mode == "SPOT" and score < 70:
        return None
    if mode == "FUTURES" and score < 80:
        return None

    # =========================
    # Regime
    # =========================
    regime = detect_market_regime(df4h, df1d, score_data)

    # Regime shift alert only
    shift = detect_regime_shift(df4h, df1d)
    if shift:
        return {
            "SignalType": "REGIME_SHIFT",
            "Symbol": symbol,
            "Regime": regime,
            "Details": shift
        }

    # =========================
    # Mode permission
    # =========================
    if mode == "SPOT" and direction == "SHORT":
        return {
            "SignalType": "MARKET_WARNING",
            "Symbol": symbol,
            "Regime": regime,
            "Message": "SPOT short = distribution (no buy)"
        }

    if mode == "SPOT" and regime not in ["REGIME_ACCUMULATION", "REGIME_MARKUP"]:
        return {
            "SignalType": "MARKET_WARNING",
            "Symbol": symbol,
            "Regime": regime,
            "Message": "No buy zone (institutional distribution)"
        }

    if mode == "FUTURES":
        if direction == "LONG" and regime not in ["REGIME_ACCUMULATION","REGIME_MARKUP"]:
            return None
        if direction == "SHORT" and regime not in ["REGIME_DISTRIBUTION","REGIME_MARKDOWN"]:
            return None

    # =========================
    # ADL confirmation
    # =========================
    adl = accumulation_distribution(df4h)
    if direction == "LONG" and adl.iloc[-1] <= adl.iloc[-10]:
        return None
    if direction == "SHORT" and adl.iloc[-1] >= adl.iloc[-10]:
        return None

    # =========================
    # SL structure
    # =========================
    if direction == "LONG":
        supports = [s for s in find_support(df1d, SR_LOOKBACK) if s < entry]
        if not supports:
            return None
        sl = max(supports) * (1 - ZONE_BUFFER)
        tp1 = entry + (entry - sl) * TP1_R
        tp2 = entry + (entry - sl) * TP2_R
        phase = "AKUMULASI_INSTITUSI"
    else:
        resistances = [r for r in find_resistance(df1d, SR_LOOKBACK) if r > entry]
        if not resistances:
            return None
        sl = min(resistances) * (1 + ZONE_BUFFER)
        tp1 = entry - (sl - entry) * TP1_R
        tp2 = entry - (sl - entry) * TP2_R
        phase = "DISTRIBUSI_INSTITUSI"

    # =========================
    # Execution confirmation
    # =========================
    if not execution_confirmation(df_ltf, direction):
        return None

    # =========================
    # Futures position size
    # =========================
    pos_size = 0.0
    if mode == "FUTURES":
        pos_size = calculate_futures_position(balance, entry, sl)
        if pos_size <= 0:
            return None

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
        "Entry": round(entry,6),
        "SL": round(sl,6),
        "TP1": round(tp1,6),
        "TP2": round(tp2,6),
        "Mode": mode,
        "Direction": direction,
        "PositionSize": pos_size
    }
