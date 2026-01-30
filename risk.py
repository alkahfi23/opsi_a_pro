# =====================================================
# OPSI A PRO — FUTURES RISK ENGINE
# =====================================================
from config import (
    FUTURES_RISK_PCT,
    FUTURES_LEVERAGE,
    FUTURES_MAX_SL,
    FUTURES_MAX_NOTIONAL
)

def calculate_futures_position(balance, entry, sl):
    stop_pct = abs(entry - sl) / entry

    # SL sanity
    if stop_pct <= 0 or stop_pct > FUTURES_MAX_SL:
        return 0.0

    # real risk
    risk_usdt = balance * FUTURES_RISK_PCT
    notional = risk_usdt / stop_pct

    # max leverage usage
    max_notional = balance * FUTURES_LEVERAGE * FUTURES_MAX_NOTIONAL

    return round(min(notional, max_notional), 2)
