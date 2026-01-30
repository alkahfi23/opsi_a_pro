# =====================================================
# OPSI A PRO — CONFIG
# =====================================================

# ===== TIMEFRAME =====
ENTRY_TF = "4h"
DAILY_TF = "1d"
LTF_TF   = "15m"

LIMIT_4H = 200
LIMIT_1D = 200
LIMIT_LTF = 100

# ===== INDICATOR =====
ATR_PERIOD = 10
SUPERTREND_MULT = 3.0

VO_FAST = 14
VO_SLOW = 28

# ===== SUPPORT / RESISTANCE =====
SR_LOOKBACK = 5
ZONE_BUFFER = 0.01

# ===== TARGET =====
TP1_R = 0.8
TP2_R = 2.0

# ===== SCANNER =====
RATE_LIMIT_DELAY = 0.15
MAX_SCAN_SYMBOLS = 120

# ===== FUTURES SAFE MODE =====
FUTURES_RISK_PCT = 0.005     # 0.5% real risk
FUTURES_LEVERAGE = 50
FUTURES_MAX_SL   = 0.015    # max SL 1.5%
FUTURES_MAX_NOTIONAL = 0.25 # use only 25% leverage power

# ===== FILE PATH =====
SIGNAL_LOG_FILE = "signal_history.csv"
TRADE_RESULT_FILE = "trade_results.csv"
FUTURES_TRADE_FILE = "futures_trades.csv"

# Futures execution
FUTURES_EXEC_TF = "15m"     # bisa 5m untuk lebih agresif
FUTURES_LTF_LIMIT = 200

