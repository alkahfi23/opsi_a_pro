import requests
import streamlit as st

BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(text: str):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    r = requests.post(TELEGRAM_URL, json=payload, timeout=10)

    # ⛔ WAJIB raise kalau gagal
    if r.status_code != 200:
        raise RuntimeError(f"Telegram error: {r.text}")


def format_signal_message(sig: dict) -> str:
    return f"""
<b>🚨 OPSI A PRO SIGNAL</b>

<b>Symbol:</b> {sig['Symbol']}
<b>Mode:</b> {sig['Mode']}
<b>Direction:</b> {sig['Direction']}
<b>Score:</b> {sig['Score']}
<b>Regime:</b> {sig['Regime']}

<b>Entry:</b> {sig['Entry']}
<b>SL:</b> {sig['SL']}
<b>TP1:</b> {sig['TP1']}
<b>TP2:</b> {sig['TP2']}

<b>Time:</b> {sig['Time']}
"""
