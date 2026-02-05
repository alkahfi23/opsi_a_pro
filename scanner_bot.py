# =====================================================
# OPSI A PRO — AUTO SCANNER BOT (FINAL)
# CRON-LIKE | SAFE | ANTI-SPAM | DAILY SUMMARY
# =====================================================

import time
import os
from datetime import datetime, timezone

from exchange import get_okx
from signals import check_signal
from history import (
    save_signal,
    auto_close_signals,
    is_symbol_in_cooldown,
    calculate_bot_rating
)
from telegram_bot import send_telegram_message
from scheduler import (
    is_optimal_spot,
    is_optimal_futures
)
from config import (
    FUTURES_BIG_COINS,
    MAX_SCAN_SYMBOLS,
    RATE_LIMIT_DELAY
)

# =====================================================
# CONFIG
# =====================================================
SCAN_INTERVAL = 300        # 5 menit
BALANCE_DUMMY = 10_000     # simulasi
SUMMARY_FLAG_FILE = "daily_summary.flag"


# =====================================================
# LOGGER
# =====================================================
def log(msg: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}", flush=True)


# =====================================================
# DAILY SUMMARY HELPERS
# =====================================================
def summary_sent_today() -> bool:
    if not os.path.exists(SUMMARY_FLAG_FILE):
        return False

    with open(SUMMARY_FLAG_FILE, "r") as f:
        last_date = f.read().strip()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return last_date == today


def mark_summary_sent():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(SUMMARY_FLAG_FILE, "w") as f:
        f.write(today)


# =====================================================
# BUILD TELEGRAM MESSAGE (PLAIN TEXT)
# =====================================================
def build_signal_message(sig: dict) -> str:
    return (
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
        f"Time       : {sig.get('TimeWIB', sig.get('Time', ''))}"
    )


# =====================================================
# SCAN MARKET
# RETURN True  = scan dilakukan
# RETURN False = skip (di luar jam)
# =====================================================
def scan_market(mode: str) -> bool:
    okx = get_okx()

    # =========================
    # TIME GUARD
    # =========================
    if mode == "FUTURES" and not is_optimal_futures():
        log("⏳ FUTURES outside optimal hours — skip")
        return False

    if mode == "SPOT" and not is_optimal_spot():
        log("⏳ SPOT outside optimal hours — skip")
        return False

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

        # ⛔ Anti duplicate / cooldown
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
        save_signal(sig)

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
            send_telegram_message(build_signal_message(sig))
            log("📩 Telegram sent")
        except Exception as e:
            log(f"❌ Telegram error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return True


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
            fut_active = scan_market("FUTURES")
            spot_active = scan_market("SPOT")

            # =========================
            # DAILY SUMMARY (1x / day)
            # =========================
            if not fut_active and not spot_active:
                if not summary_sent_today():
                    stats = calculate_bot_rating()

                    if stats and stats.get("valid"):
                        send_telegram_message(
                            "OPSI A PRO — DAILY SUMMARY\n\n"
                            f"Rating     : {stats['rating']}\n"
                            f"Win Rate   : {stats['win_rate']}%\n"
                            f"Expectancy : {stats['expectancy']} R\n"
                            f"Trades     : {stats['trades']}\n\n"
                            "Market currently outside optimal hours"
                        )
                        mark_summary_sent()
                        log("📊 Daily summary sent")

            else:
                log("📡 Active session — summary skipped")

        except Exception as e:
            log(f"🔥 Scanner crash prevented: {e}")

        time.sleep(SCAN_INTERVAL)
