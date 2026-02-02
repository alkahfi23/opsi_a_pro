# =====================================================
# OPSI A PRO — CONFIG
# FINAL | CLEAN | PROP-FIRM GRADE
# =====================================================


# =====================================================
# TIMEFRAME
# =====================================================
ENTRY_TF = "4h"
DAILY_TF = "1d"

# Lower Timeframe (execution)
LTF_TF = "15m"          # safe default (5m = aggressive)

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
ZONE_BUFFER = 0.01      # 1% buffer beyond structure


# =====================================================
# TARGET (R MULTIPLIER)
# =====================================================
TP1_R = 0.8
TP2_R = 2.0


# =====================================================
# SCANNER
# =====================================================
RATE_LIMIT_DELAY = 0.15
MAX_SCAN_SYMBOLS = 120      # ONLY for SPOT


# =====================================================
# FUTURES — RISK MANAGEMENT (HARD RULES)
# =====================================================

# Real equity risk per trade (0.5%)
FUTURES_RISK_PCT = 0.005

# 🔥 HARD LEVERAGE CAP (MAX 50x)
FUTURES_LEVERAGE = 50

# Max allowed stop distance (1.5%)
FUTURES_MAX_RISK = 0.015

# Use only part of leverage power (extra safety)
# Example: 0.25 → max notional = balance * leverage * 25%
FUTURES_MAX_NOTIONAL = 0.25


# =====================================================
# FUTURES EXECUTION (LTF ENTRY)
# =====================================================
FUTURES_EXEC_TF = "15m"      # recommended: 15m (safe), 5m (aggressive)
FUTURES_LTF_LIMIT = 200


# =====================================================
# FUTURES — BIG COIN UNIVERSE (HARD FILTER)
# PROP / INSTITUTIONAL GRADE
# =====================================================
# 👉 Futures hanya untuk coin besar & likuid
# 👉 Menghindari SL liar, spread besar, fake wick

FUTURES_BIG_COINS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "AVAX/USDT",
    "DOGE/USDT",
    "LINK/USDT",
    "LTC/USDT",
    "BCH/USDT",
    "OP/USDT",
    "ARB/USDT",
    "SUI/USDT",
    "APT/USDT"
]


# =====================================================
# FILE PATH
# =====================================================
SIGNAL_LOG_FILE    = "signal_history.csv"
TRADE_RESULT_FILE  = "trade_results.csv"
FUTURES_TRADE_FILE = "futures_trades.csv"
