# =====================================================
# OPSI A PRO — TELEGRAM NOTIFIER
# =====================================================

import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLE


def send_telegram_message(text: str):
    if not TELEGRAM_ENABLE:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass
        
def format_signal_message(sig: dict) -> str:
    return f"""
🚨 *NEW SIGNAL — {sig['Mode']}*

📌 *Symbol:* `{sig['Symbol']}`
📈 *Direction:* {sig['Direction']}
🧠 *Regime (Entry):* {sig['Regime']}
⭐ *Score:* {sig['Score']}

💰 *Entry:* `{sig['Entry']}`
🛑 *Execution SL:* `{sig['SL']}`
⚠️ *Invalidation SL:* `{sig.get('SL_Invalidation')}`

🎯 *TP1:* `{sig['TP1']}`
🎯 *TP2:* `{sig['TP2']}`

📦 *Position Size:* `{sig['PositionSize']}`

⏰ {sig['Time']}
"""
