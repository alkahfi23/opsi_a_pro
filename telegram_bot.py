# telegram_bot.py

import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Telegram env vars not set")


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)


# =========================
# ENTRY SIGNAL MESSAGE
# =========================
def format_signal_message(sig: dict) -> str:
    return (
        f"🚀 *OPSI A PRO SIGNAL*\n\n"
        f"*Symbol:* {sig['Symbol']}\n"
        f"*Mode:* {sig['Mode']}\n"
        f"*Direction:* {sig['Direction']}\n"
        f"*Score:* {sig['Score']}\n"
        f"*Regime:* {sig['Regime']}\n\n"
        f"*Entry:* {sig['Entry']}\n"
        f"*SL:* {sig['SL']}\n"
        f"*TP1:* {sig['TP1']}\n"
        f"*TP2:* {sig['TP2']}\n"
        f"_Time:_ {sig['Time']}"
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
