# telegram_bot.py (FINAL)

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
