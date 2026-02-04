# =====================================================
# OPSI A PRO — AUTO SCANNER BOT (RENDER)
# 24/7 | OPTIMAL HOURS | TELEGRAM ONLY
# =====================================================

import time
from datetime import datetime

from exchange import get_okx
from config import (
    RATE_LIMIT_DELAY,
    MAX_SCAN_SYMBOLS,
    FUTURES_BIG_COINS
)
from signals import check_signal
from history import (
    load_signal_history,
    save_signal,
    auto_close_signals,
    monitor_regime_flip
)
from telegram_bot import send_telegram_message, format_signal_message
from utils import is_safe_spot_time, is_safe_futures_time


SCAN_INTERVAL = 60 * 5   # check setiap 5 menit
MODE = "FUTURES"         # atau SPOT
BALANCE = 10000


def run_scan():
    okx = get_okx()

    if MODE == "FUTURES" and not is_safe_futures_time():
        return

    if MODE == "SPOT" and not is_safe_spot_time():
        return

    symbols = (
        FUTURES_BIG_COINS
        if MODE == "FUTURES"
        else [
            s for s, m in okx.markets.items()
            if m.get("spot") and m.get("active") and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]
    )

    for symbol in symbols:
        try:
            sig = check_signal(symbol, MODE, BALANCE)
        except Exception:
            continue

        if sig and sig.get("SignalType") == "TRADE_EXECUTION":
            before = len(load_signal_history())
            save_signal(sig)
            after = len(load_signal_history())

            if after > before:
                msg = format_signal_message(sig)
                send_telegram_message(msg)

        time.sleep(RATE_LIMIT_DELAY)


if __name__ == "__main__":
    print("🚀 OPSI AUTO SCANNER STARTED")

    while True:
        try:
            auto_close_signals()      # TP / SL
            monitor_regime_flip()     # regime flip
            run_scan()
        except Exception as e:
            print("Scanner error:", e)

        time.sleep(SCAN_INTERVAL)
