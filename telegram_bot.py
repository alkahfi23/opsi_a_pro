# =====================================================
# OPSI A PRO — TELEGRAM BOT CORE
# FINAL | HTML MODE | RENDER SAFE
# =====================================================

import os
import requests


# =====================================================
# ENV CONFIG (RENDER / VPS / DOCKER)
# =====================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError(
        "❌ TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set"
    )

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# =====================================================
# SEND MESSAGE (HTML SAFE)
# =====================================================
def send_telegram_message(text: str):
    """
    Send message to Telegram using HTML parse mode
    """

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    r = requests.post(
        TELEGRAM_URL,
        json=payload,
        timeout=15
    )

    if r.status_code != 200:
        raise RuntimeError(
            f"Telegram API error {r.status_code}: {r.text}"
        )


# =====================================================
# FORMAT — ENTRY SIGNAL
# =====================================================
def format_signal_message(sig: dict) -> str:
    """
    Format ENTRY signal (HTML safe)
    """

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
# FORMAT — TRADE UPDATE (TP / SL)
# =====================================================
def format_trade_update(row: dict) -> str:
    """
    Format TP / SL update (HTML safe)
    """

    status_emoji = {
        "TP1 HIT": "🟡",
        "TP2 HIT": "🟢",
        "SL HIT": "🔴"
    }.get(row.get("Status"), "⚠️")

    return (
        f"{status_emoji} <b>OPSI A PRO TRADE UPDATE</b>\n\n"
        f"<b>Symbol:</b> {row['Symbol']}\n"
        f"<b>Mode:</b> {row['Mode']}\n"
        f"<b>Direction:</b> {row['Direction']}\n"
        f"<b>Status:</b> {row['Status']}\n\n"
        f"<b>Entry:</b> {row['Entry']}\n"
        f"<b>SL:</b> {row['SL']}\n"
        f"<b>TP1:</b> {row['TP1']}\n"
        f"<b>TP2:</b> {row['TP2']}"
    )


# =====================================================
# FORMAT — REGIME FLIP ALERT
# =====================================================
def format_regime_flip(symbol, old_regime, new_regime) -> str:
    return (
        f"🚨 <b>REGIME FLIP ALERT</b>\n\n"
        f"<b>Symbol:</b> {symbol}\n"
        f"<b>From:</b> {old_regime}\n"
        f"<b>To:</b> {new_regime}\n\n"
        f"⚠️ <i>Position still OPEN</i>\n"
        f"Consider risk reduction"
    )
