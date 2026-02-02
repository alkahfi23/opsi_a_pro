# =====================================================
# OPSI A PRO — CONFIG (FINAL, CLEAN, CONSISTENT)
# =====================================================

# =====================================================
# TIMEFRAME
# =====================================================
ENTRY_TF = "4h"          # HTF structure
DAILY_TF = "1d"          # Macro regime
LTF_TF   = "15m"         # Default execution TF (can switch to 5m)

LIMIT_4H  = 200
LIMIT_1D  = 200
LIMIT_LTF = 200


# =====================================================
# INDICATOR CONFIG
# =====================================================
ATR_PERIOD = 10
SUPERTREND_MULT = 3.0

VO_FAST = 14
VO_SLOW = 28


# =====================================================
# SUPPORT / RESISTANCE
# =====================================================
SR_LOOKBACK = 5
ZONE_BUFFER = 0.01       # 1% buffer beyond structure


# =====================================================
# TARGET (R MULTIPLIER)
# =====================================================
TP1_R = 0.8
TP2_R = 2.0


# =====================================================
# SCANNER
# =====================================================
RATE_LIMIT_DELAY = 0.15
MAX_SCAN_SYMBOLS = 120


# =====================================================
# FUTURES — RISK MANAGEMENT (HARD RULES)
# =====================================================

# Real equity risk per trade (0.5%)
FUTURES_RISK_PCT = 0.005

# 🔥 HARD LEVERAGE CAP (MAX 50x)
FUTURES_LEVERAGE = 50

# Max stop loss distance (1.5%)
FUTURES_MAX_RISK = 0.015

# Use only part of leverage capacity (extra safety)
# Example: 0.25 → max notional = balance * leverage * 0.25
FUTURES_MAX_NOTIONAL = 0.25


# =====================================================
# FUTURES — BIG COIN FILTER (REKOMENDASI KERAS)
# =====================================================
# Futures ONLY allowed for high-liquidity institutional coins
# Small / meme / low OI coins → AUTO SKIP for futures

FUTURES_ALLOWED_SYMBOLS = [
    # CORE MAJORS
    "BTC/USDT",
    "ETH/USDT",

    # LARGE CAP LIQUID
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",

    # INSTITUTIONAL ALTS
    "LINK/USDT",
    "AVAX/USDT",
    "MATIC/USDT",
    "ARB/USDT",
    "OP/USDT",
    "APT/USDT"
]


# =====================================================
# FUTURES EXECUTION (LTF ENTRY)
# =====================================================
FUTURES_EXEC_TF   = "15m"     # recommended: 15m (safe), 5m (aggressive)
FUTURES_LTF_LIMIT = 200


# =====================================================
# FILE PATH
# =====================================================
SIGNAL_LOG_FILE    = "signal_history.csv"
TRADE_RESULT_FILE = "trade_results.csv"
FUTURES_TRADE_FILE = "futures_trades.csv"
