# =====================================================
# OPSI A PRO — TELEGRAM BOT CORE
# FINAL | HTML MODE | RENDER SAFE | NO CRASH
# =====================================================

import os
import requests
from datetime import datetime


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    if BOT_TOKEN else None
)


# =====================================================
# SAFE LOGGER
# =====================================================
def _log(msg: str):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


# =====================================================
# SEND MESSAGE (SAFE)
# =====================================================
def send_telegram_message(text: str):
    """
    Safe Telegram sender (never crash app)
    """

    if not BOT_TOKEN or not CHAT_ID:
        _log("⚠️ Telegram ENV not set — message skipped")
        return False

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(
            TELEGRAM_URL,
            json=payload,
            timeout=15
        )

        if r.status_code != 200:
            _log(f"❌ Telegram API error {r.status_code}: {r.text}")
            return False

        return True

    except Exception as e:
        _log(f"❌ Telegram request failed: {e}")
        return False


# =====================================================
# FORMAT — ENTRY SIGNAL
# =====================================================
def format_signal_message(sig: dict) -> str:
    return (
        f"🚀 <b>OPSI A PRO SIGNAL</b>\n\n"
        f"<b>Symbol:</b> {sig['Symbol']}\n"
        f"<b>Mode:</b> {sig['Mode']}\n"
        f"<b>Direction:</b> {sig['Direction']}\n"
        f"<b>Score:</b> {sig['Score']}\n"
        f"<b>Regime:</b> {sig['Regime']}\n\n"
        f"<b>Entry:</b> {sig['Entry']}\n"
        f"<b>SL:</b> {sig['SL']}\n"
        f"<b>TP1:</b> {sig['TP1']}\n"
        f"<b>TP2:</b> {sig['TP2']}\n\n"
        f"⏰ <i>{sig['Time']}</i>"
    )


# =====================================================
# FORMAT — TRADE UPDATE
# =====================================================
def format_trade_update(row: dict) -> str:
    emoji = {
        "TP1 HIT": "🟡",
        "TP2 HIT": "🟢",
        "SL HIT": "🔴"
    }.get(row.get("Status"), "⚠️")

    return (
        f"{emoji} <b>OPSI A PRO TRADE UPDATE</b>\n\n"
        f"<b>Symbol:</b> {row['Symbol']}\n"
        f"<b>Mode:</b> {row['Mode']}\n"
        f"<b>Direction:</b> {row['Direction']}\n"
        f"<b>Status:</b> {row['Status']}\n\n"
        f"<b>Entry:</b> {row['Entry']}\n"
        f"<b>SL:</b> {row['SL']}\n"
        f"<b>TP1:</b> {row['TP1']}\n"
        f"<b>TP2:</b> {row['TP2']}"
    )
