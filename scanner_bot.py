# =====================================================
# OPSI A PRO — AUTO SCANNER BOT
# CRON-LIKE | RENDER SAFE | NO STREAMLIT | CLEAN
# =====================================================

import time
from datetime import datetime, timezone

from exchange import get_okx
from signals import check_signal
from history import (
    save_signal,
    auto_close_signals,
    is_symbol_in_cooldown,
    calculate_bot_rating,
)
from telegram_bot import send_telegram_message
from scheduler import is_optimal_spot, is_optimal_futures
from config import (
    FUTURES_BIG_COINS,
    MAX_SCAN_SYMBOLS,
    RATE_LIMIT_DELAY,
)

# =====================================================
# CONFIG
# =====================================================
SCAN_INTERVAL = 300        # 5 menit
BALANCE_DUMMY = 10_000     # simulasi only


# =====================================================
# LOGGER
# =====================================================
def log(msg: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}", flush=True)


# =====================================================
# TELEGRAM MESSAGE BUILDER (PLAIN TEXT)
# =====================================================
def build_message(sig: dict, stats: dict | None):
    msg = (
        "OPSI A PRO SIGNAL\n\n"
        f"Symbol     : {sig['Symbol']}\n"
        f"Mode       : {sig['Mode']}\n"
        f"Direction  : {sig['Direction']}\n"
        f"Score      : {sig['Score']}\n"
        f"Regime     : {sig['Regime']}\n\n"
        f"Entry      : {sig['Entry']}\n"
        f"SL         : {sig['SL']}\n"
        f"TP1        : {sig['TP1']}\n"
        f"TP2        : {sig['TP2']}\n"
        f"Time       : {sig.get('TimeWIB', '')}\n"
    )

    if stats and stats.get("valid"):
        msg += (
            "\nBOT PERFORMANCE\n"
            f"Rating     : {stats['rating']}\n"
            f"Win Rate   : {stats['win_rate']}%\n"
            f"Expectancy : {stats['expectancy']} R\n"
            f"Trades     : {stats['trades']}\n"
        )

    return msg


# =====================================================
# SCAN MARKET
# =====================================================
def scan_market(mode: str):
    okx = get_okx()

    # =========================
    # TIME FILTER
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

        # ⛔ COOLDOWN CHECK
        if is_symbol_in_cooldown(symbol, mode):
            continue

        try:
            sig = check_signal(symbol, mode, BALANCE_DUMMY)
        except Exception as e:
            log(f"⚠️ Signal error {symbol}: {e}")
            continue

        if not sig or sig.get("SignalType") != "TRADE_EXECUTION":
            continue

        # =========================
        # SAVE SIGNAL
        # =========================
        try:
            save_signal(sig)
        except Exception as e:
            log(f"❌ Save signal failed {symbol}: {e}")
            continue

        log(
            f"✅ SIGNAL {symbol} | "
            f"{sig['Direction']} | "
            f"Score {sig['Score']} | "
            f"{sig['Regime']}"
        )

        # =========================
        # TELEGRAM ALERT
        # =========================
        try:
            stats = calculate_bot_rating()
            msg = build_message(sig, stats)
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
            # MARKET SCANS
            # =========================
            scan_market("FUTURES")
            scan_market("SPOT")

            log("😴 Cycle complete — waiting next run")

        except Exception as e:
            log(f"🔥 Scanner crash prevented: {e}")

        time.sleep(SCAN_INTERVAL)
