# =====================================================
# OPSI A PRO — AUTO SCANNER BOT
# CRON-LIKE | RENDER SAFE
# =====================================================

import time
from exchange import get_okx
from signals import check_signal
from history import save_signal, auto_close_signals
from telegram_bot import send_telegram_message, format_signal_message
from scheduler import is_optimal_spot, is_optimal_futures
from config import (
    FUTURES_BIG_COINS,
    MAX_SCAN_SYMBOLS,
    RATE_LIMIT_DELAY
)

# =========================
# CONFIG
# =========================
SCAN_INTERVAL = 300  # 5 menit
BALANCE_DUMMY = 10_000  # tidak eksekusi real


def scan_market(mode: str):
    okx = get_okx()

    if mode == "FUTURES" and not is_optimal_futures():
        return

    if mode == "SPOT" and not is_optimal_spot():
        return

    symbols = (
        FUTURES_BIG_COINS
        if mode == "FUTURES"
        else [
            s for s, m in okx.markets.items()
            if m.get("spot") and m.get("active") and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]
    )

    for symbol in symbols:
        try:
            sig = check_signal(symbol, mode, BALANCE_DUMMY)
        except Exception:
            continue

        if sig and sig["SignalType"] == "TRADE_EXECUTION":
            save_signal(sig)

            try:
                msg = format_signal_message(sig)
                send_telegram_message(msg)
            except Exception:
                pass

        time.sleep(RATE_LIMIT_DELAY)


# =========================
# MAIN LOOP (CRON-LIKE)
# =========================
if __name__ == "__main__":
    while True:
        try:
            auto_close_signals()      # TP / SL alert
            scan_market("FUTURES")    # auto futures
            scan_market("SPOT")       # auto spot
        except Exception as e:
            print("Scanner error:", e)

        time.sleep(SCAN_INTERVAL)
