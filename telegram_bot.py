# =====================================================
# OPSI A PRO — TELEGRAM BOT (DUAL MODE)
# Streamlit UI + Render Worker SAFE
# =====================================================

import os
import requests

# =========================
# TOKEN LOADING (SAFE)
# =========================
BOT_TOKEN = None
CHAT_ID = None

# Try ENV (Render / Production)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fallback to Streamlit secrets (UI only)
if BOT_TOKEN is None or CHAT_ID is None:
    try:
        import streamlit as st
        BOT_TOKEN = BOT_TOKEN or st.secrets.get("TELEGRAM_BOT_TOKEN")
        CHAT_ID = CHAT_ID or st.secrets.get("TELEGRAM_CHAT_ID")
    except Exception:
        pass


if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("❌ Telegram token / chat_id not found")


API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# =====================================================
# SEND MESSAGE
# =====================================================
def send_telegram_message(text: str):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    r = requests.post(API_URL, json=payload, timeout=10)
    if not r.ok:
        raise RuntimeError(r.text)


# =====================================================
# FORMAT ENTRY SIGNAL
# =====================================================
def format_signal_message(sig: dict) -> str:
    return f"""
🚀 *NEW SIGNAL*
━━━━━━━━━━━━
*Symbol:* `{sig['Symbol']}`
*Mode:* {sig['Mode']}
*Direction:* {sig['Direction']}
*Score:* {sig['Score']}
*Regime:* {sig['Regime']}

*Entry:* {sig['Entry']}
*SL:* {sig['SL']}
*TP1:* {sig['TP1']}
*TP2:* {sig['TP2']}

⏰ {sig['Time']}
""".strip()


# =====================================================
# FORMAT TRADE UPDATE (TP / SL)
# =====================================================
def format_trade_update(row: dict) -> str:
    return f"""
📢 *TRADE UPDATE*
━━━━━━━━━━━━
*Symbol:* `{row['Symbol']}`
*Status:* {row['Status']}
*Mode:* {row['Mode']}
*Direction:* {row['Direction']}

*Entry:* {row['Entry']}
*Last SL:* {row['SL']}
*TP1:* {row['TP1']}
*TP2:* {row['TP2']}
""".strip()
