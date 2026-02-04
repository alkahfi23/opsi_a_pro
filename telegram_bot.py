# =====================================================
# OPSI A PRO — TELEGRAM BOT CORE
# FINAL | RENDER SAFE | NO STREAMLIT | ANTI SILENT FAIL
# =====================================================

import os
import requests
from datetime import datetime

# =====================================================
# ENV (RENDER)
# =====================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError(
        "❌ TELEGRAM ENV NOT SET. "
        "Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in Render."
    )

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# =====================================================
# CORE SENDER
# =====================================================
def send_telegram_message(text: str):
    """
    Safe Telegram sender with response validation
    """

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",   # 🔥 HTML = SAFE (no markdown crash)
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(
            TELEGRAM_URL,
            json=payload,
            timeout=10
        )
    except Exception as e:
        raise RuntimeError(f"Telegram request failed: {e}")

    # =========================
    # VALIDATE RESPONSE
    # =========================
    if r.status_code != 200:
        raise RuntimeError(
            f"Telegram API error {r.status_code}: {r.text}"
        )

    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram rejected message: {data}"
        )


# =====================================================
# SIGNAL MESSAGE (ENTRY)
# =====================================================
def format_signal_message(sig: dict) -> str:
    return (
        f"🚀 <b>OPSI A PRO — NEW SIGNAL</b>\n\n"
        f"<b>Symbol:</b> {sig['Symbol']}\n"
        f"<b>Mode:</b> {sig['Mode']}\n"
        f"<b>Side:</b> {sig['Direction']}\n"
        f"<b>Score:</b> {sig['Score']}\n"
        f"<b>Regime:</b> {sig['Regime']}\n\n"
        f"<b>Entry:</b> {sig['Entry']}\n"
        f"<b>SL:</b> {sig['SL']}\n"
        f"<b>TP1:</b> {sig['TP1']}\n"
        f"<b>TP2:</b> {sig['TP2']}\n\n"
        f"⏰ <i>{sig['Time']}</i>"
    )


# =====================================================
# TRADE UPDATE (TP / SL)
# =====================================================
def format_trade_update(row: dict) -> str:
    return (
        f"⚠️ <b>OPSI A PRO — TRADE UPDATE</b>\n\n"
        f"<b>Symbol:</b> {row['Symbol']}\n"
        f"<b>Mode:</b> {row['Mode']}\n"
        f"<b>Direction:</b> {row['Direction']}\n"
        f"<b>Status:</b> {row['Status']}\n\n"
        f"<b>Entry:</b> {row['Entry']}\n"
        f"<b>SL:</b> {row['SL']}\n"
        f"<b>TP1:</b> {row['TP1']}\n"
        f"<b>TP2:</b> {row['TP2']}\n\n"
        f"⏰ <i>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
    )


# =====================================================
# REGIME FLIP ALERT
# =====================================================
def format_regime_flip(symbol, old_regime, new_regime) -> str:
    return (
        f"🚨 <b>REGIME FLIP ALERT</b>\n\n"
        f"<b>Symbol:</b> {symbol}\n"
        f"<b>From:</b> {old_regime}\n"
        f"<b>To:</b> {new_regime}\n\n"
        f"⚠️ Position still OPEN\n"
        f"Consider reducing risk"
    )
