# =====================================================
# TELEGRAM BOT — CORE (NO STREAMLIT)
# =====================================================

import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Telegram ENV not set")

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    r = requests.post(TELEGRAM_URL, json=payload, timeout=10)

    # 🔥 PENTING: VALIDASI RESPONSE
    if r.status_code != 200:
        raise RuntimeError(
            f"Telegram API error {r.status_code}: {r.text}"
        )


def format_signal_message(sig: dict) -> str:
    return (
        f"🚀 *OPSI A PRO SIGNAL*\n\n"
        f"Symbol : `{sig['Symbol']}`\n"
        f"Mode   : {sig['Mode']}\n"
        f"Side   : {sig['Direction']}\n"
        f"Score  : {sig['Score']}\n"
        f"Regime : {sig['Regime']}\n\n"
        f"Entry  : {sig['Entry']}\n"
        f"SL     : {sig['SL']}\n"
        f"TP1    : {sig['TP1']}\n"
        f"TP2    : {sig['TP2']}\n\n"
        f"⏰ {sig['Time']}"
    )


# =========================
# TRADE UPDATE MESSAGE (TP / SL)
# =========================
def format_trade_update(row: dict) -> str:
    return (
        f"⚠️ *OPSI A PRO TRADE UPDATE*\n\n"
        f"*Symbol:* {row['Symbol']}\n"
        f"*Mode:* {row['Mode']}\n"
        f"*Direction:* {row['Direction']}\n"
        f"*Status:* {row['Status']}\n\n"
        f"*Entry:* {row['Entry']}\n"
        f"*SL:* {row['SL']}\n"
        f"*TP1:* {row['TP1']}\n"
        f"*TP2:* {row['TP2']}"
    )
