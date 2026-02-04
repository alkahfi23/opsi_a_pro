# =====================================================
# OPSI A PRO — AUTO SCANNER BOT
# CRON-LIKE | RENDER SAFE | CLEAN LOG | TELEGRAM READY
# =====================================================

# =========================
# ENV & WARNING SUPPRESS
# =========================
import os
import warnings

os.environ["STREAMLIT_SUPPRESS_CONFIG_WARNINGS"] = "1"
warnings.filterwarnings("ignore")

# =========================
# CORE IMPORT
# =========================
import time
from datetime import datetime, timezone

from exchange import get_okx
from signals import check_signal
from history import (
    save_signal,
    auto_close_signals,
    load_signal_history
)
from telegram_bot import (
    send_telegram_message,
    format_signal_message
)
from scheduler import (
    is_optimal_spot,
    is_optimal_futures
)
from config import (
    FUTURES_BIG_COINS,
    MAX_SCAN_SYMBOLS,
    RATE_LIMIT_DELAY
)

# =========================
# CONFIG
# =========================
SCAN_INTERVAL = 300        # 5 menit
BALANCE_DUMMY = 10_000     # simulasi only (no execution)

# =========================
# LOGGER (UTC SAFE)
# =========================
def log(msg: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}", flush=True)


# =====================================================
# DUPLICATE CHECK (ANTI SPAM)
# =====================================================
def is_new_signal(symbol: str, mode: str) -> bool:
    """
    Prevent duplicate signal spam per symbol & mode
    """
    df = load_signal_history()
    if df.empty:
        return True

    recent = df[
        (df["Symbol"] == symbol) &
        (df["Mode"] == mode) &
        (df["Status"] == "OPEN")
    ]

    return recent.empty


# =====================================================
# SCAN FUNCTION
# =====================================================
def scan_market(mode: str):
    okx = get_okx()

    # =========================
    # TIME GUARD
    # =========================
    if mode == "FUTURES" and not is_optimal_futures():
        log("⏳ FUTURES outside optimal hours — skip")
        return

    if mode == "SPOT" and not is_optimal_spot():
        log("⏳ SPOT outside optimal hours — skip")
        return

    # =========================
    # SYMBOL UNIVERSE
    # =========================
    symbols = (
        FUTURES_BIG_COINS
        if mode == "FUTURES"
        else [
            s for s, m in okx.markets.items()
            if m.get("spot") and m.get("active") and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]
    )

    log(f"🔍 Scanning {mode} — {len(symbols)} symbols")

    # =========================
    # MAIN LOOP
    # =========================
    for symbol in symbols:
        try:
            sig = check_signal(symbol, mode, BALANCE_DUMMY)
        except Exception as e:
            log(f"⚠️ Signal error {symbol}: {e}")
            continue

        if sig and sig.get("SignalType") == "TRADE_EXECUTION":

            # =========================
            # ANTI DUPLICATE
            # =========================
            if not is_new_signal(symbol, mode):
                continue

            save_signal(sig)
            log(
                f"✅ SIGNAL {symbol} {sig['Direction']} | "
                f"Score {sig['Score']} | {sig['Regime']}"
            )

            # =========================
            # TELEGRAM ALERT
            # =========================
            try:
                msg = format_signal_message(sig)
                send_telegram_message(msg)
                log("📩 Telegram sent")
            except Exception as e:
                log(f"❌ Telegram error: {e}")

        time.sleep(RATE_LIMIT_DELAY)


# =====================================================
# MAIN LOOP (CRON-LIKE)
# =====================================================
if __name__ == "__main__":
    log("🚀 OPSI A PRO Scanner started")

    while True:
        try:
            # =========================
            # AUTO MAINTENANCE
            # =========================
            auto_close_signals()
            log("🔧 Auto maintenance done")

            # =========================
            # SCANS
            # =========================
            scan_market("FUTURES")
            scan_market("SPOT")

            log("😴 Cycle complete — waiting next run")

        except Exception as e:
            log(f"🔥 Scanner crash prevented: {e}")

        time.sleep(SCAN_INTERVAL)
