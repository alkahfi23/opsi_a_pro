# =====================================================
# OPSI A PRO — FUTURES RISK ENGINE (MAX 50x, SAFE MODE)
# =====================================================

from config import (
    FUTURES_RISK_PCT,
    FUTURES_LEVERAGE,
    FUTURES_MAX_RISK,
    FUTURES_MAX_NOTIONAL
)


def calculate_futures_position(balance, entry, sl):
    """
    Calculate futures position size (USDT notional)

    Rules:
    - Max leverage capped by FUTURES_LEVERAGE (50x)
    - Only use FUTURES_MAX_NOTIONAL of leverage power
    - Max SL distance capped by FUTURES_MAX_RISK (1.5%)
    - Real risk per trade = FUTURES_RISK_PCT (0.5%)

    Returns:
    - position size in USDT (float)
    - 0.0 if risk invalid
    """

    # =========================
    # STOP DISTANCE
    # =========================
    stop_pct = abs(entry - sl) / entry

    if stop_pct <= 0:
        return 0.0

    # SL too wide → reject futures trade
    if stop_pct > FUTURES_MAX_RISK:
        return 0.0

    # =========================
    # REAL RISK (USDT)
    # =========================
    risk_amount = balance * FUTURES_RISK_PCT

    # =========================
    # POSITION BY RISK
    # =========================
    position_value = risk_amount / stop_pct

    # =========================
    # MAX NOTIONAL (LEVERAGE CAP)
    # =========================
    max_position = (
        balance
        * FUTURES_LEVERAGE
        * FUTURES_MAX_NOTIONAL
    )

    # =========================
    # FINAL POSITION SIZE
    # =========================
    return round(min(position_value, max_position), 2)
