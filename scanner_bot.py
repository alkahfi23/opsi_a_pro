# =====================================================
# OPSI A PRO — SCANNER BOT
# FILE : scanner_bot.py
# CRON-LIKE | RENDER SAFE | CLEAN LOG | ANTI DUPLICATE
# =====================================================

import time
from datetime import datetime

from exchange import get_okx
from signals import check_signal
from history import (
    save_signal,
    auto_close_signals,
    is_symbol_in_cooldown,
    calculate_bot_rating,
    should_send_rating
)
from telegram_bot import send_telegram_message
from scheduler import is_optimal_spot, is_optimal_futures
from config import (
    FUTURES_BIG_COINS,
    MAX_SCAN_SYMBOLS,
    RATE_LIMIT_DELAY
)

# =====================================================
# CONFIG
# =====================================================
SCAN_INTERVAL = 300        # 5 menit
BALANCE_DUMMY = 10_000     # simulasi only (no execution)

# =====================================================
# SIMPLE LOGGER
# =====================================================
def log(msg: str):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}", flush=True)


# =====================================================
# TELEGRAM MESSAGE (SAFE — NO MARKDOWN)
# =====================================================
def build_telegram_message(sig: dict) -> str:
    return (
        "🚀 OPSI A PRO SIGNAL\n\n"
        f"Symbol     : {sig['Symbol']}\n"
        f"Mode       : {sig['Mode']}\n"
        f"Direction  : {sig['Direction']}\n"
        f"Score      : {sig['Score']}\n"
        f"Regime     : {sig['Regime']}\n\n"
        f"Entry      : {sig['Entry']}\n"
        f"SL         : {sig['SL']}\n"
        f"TP1        : {sig['TP1']}\n"
        f"TP2        : {sig['TP2']}"
    )


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
            if m.get("spot") and m.get("active")
            and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]
    )

    log(f"🔍 Scanning {mode} — {len(symbols)} symbols")

    # =========================
    # MAIN LOOP
    # =========================
    for symbol in symbols:

        # ⛔ ANTI DUPLICATE
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
            send_telegram_message(
                build_telegram_message(sig)
            )
            log("📩 Telegram signal sent")
        except Exception as e:
            log(f"❌ Telegram error: {e}")

        # =========================
        # BOT PERFORMANCE SNAPSHOT
        # =========================
        try:
            if should_send_rating():
                stats = calculate_bot_rating()
                if stats and stats.get("valid"):
                    send_telegram_message(
                        "📊 BOT PERFORMANCE\n\n"
                        f"Rating     : {stats['rating']}\n"
                        f"Win Rate   : {stats['win_rate']}%\n"
                        f"Expectancy : {stats['expectancy']} R\n"
                        f"Trades     : {stats['trades']}"
                    )
                    log("📊 Bot rating sent")
        except Exception:
            pass

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

            # =========================
            # MARKET SCANS
            # =========================
            scan_market("FUTURES")
            scan_market("SPOT")

            log("😴 Cycle complete — waiting next run")

        except Exception as e:
            log(f"🔥 Scanner crash prevented: {e}")

        time.sleep(SCAN_INTERVAL)
