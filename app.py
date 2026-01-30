# =====================================================
# OPSI A PRO — MAIN APP
# =====================================================
import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go

from exchange import get_okx
from utils import (
    is_danger_time,
    is_safe_spot_time,
    is_safe_futures_time,
    wib_hour
)
from config import RATE_LIMIT_DELAY, MAX_SCAN_SYMBOLS
from signals import check_signal
from history import load_signal_history, save_signal, auto_close_signals
from montecarlo import run_monte_carlo

# =====================================================
# PAGE
# =====================================================
st.set_page_config("OPSI A PRO — MODULAR", layout="wide")
st.title("🚀 OPSI A PRO — SPOT & FUTURES (Institutional)")

okx = get_okx()
auto_close_signals(okx)

MODE = st.radio("🧭 Trading Mode", ["SPOT","FUTURES"], horizontal=True)
BALANCE = st.number_input("💰 Account Balance (USDT)", value=10000.0, step=100.0)

hour = wib_hour()

# =====================================================
# TIME WARNINGS
# =====================================================
if is_danger_time():
    st.error(
        f"⛔ JAM BAHAYA ({hour}:00 WIB)\n\n"
        "Likuiditas rendah • Fake move tinggi"
    )
elif MODE == "FUTURES" and not is_safe_futures_time():
    st.warning("⚠️ Futures di luar jam optimal (19–23 WIB)")
elif MODE == "SPOT" and not is_safe_spot_time():
    st.warning("⚠️ Spot di luar jam ideal")

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3 = st.tabs([
    "📡 Scan Market",
    "📜 Signal History",
    "🎲 Monte Carlo"
])

# =====================================================
# TAB 1 — SCAN
# =====================================================
with tab1:
    if st.button("🔍 Scan Market"):
        symbols = [
            s for s,m in okx.markets.items()
            if m.get("spot") and m.get("active") and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]

        found = []
        progress = st.progress(0.0)
        status = st.empty()

        for i,s in enumerate(symbols,1):
            status.info(f"Scanning {s} ({i}/{len(symbols)})")

            sig = check_signal(okx, s, MODE, BALANCE)

            if sig and sig["SignalType"] == "TRADE_EXECUTION":
                save_signal(sig)
                found.append(sig)

            progress.progress(i/len(symbols))
            time.sleep(RATE_LIMIT_DELAY)

        if found:
            st.success(f"🔥 Found {len(found)} A+ setups")
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Tidak ada setup A+ ditemukan")

# =====================================================
# TAB 2 — HISTORY
# =====================================================
with tab2:
    df = load_signal_history()
    st.metric("Total Signals", len(df))
    st.metric("OPEN Signals", (df["Status"]=="OPEN").sum())
    st.dataframe(df.sort_values("Time", ascending=False), use_container_width=True)

    st.download_button(
        "⬇️ Download History",
        df.to_csv(index=False),
        "signal_history.csv"
    )

# =====================================================
# TAB 3 — MONTE CARLO
# =====================================================
with tab3:
    try:
        trade_results = pd.read_csv("trade_results.csv")
    except:
        trade_results = pd.DataFrame()

    if trade_results.empty:
        st.warning("Trade result belum cukup")
    else:
        risk = st.slider("Risk / Trade (%)", 0.2, 3.0, 1.0)/100
        trades = st.slider("Trades / Simulation", 50, 500, 300)

        if st.button("🎲 Run Monte Carlo"):
            res = run_monte_carlo(
                trade_results,
                load_signal_history(),
                risk,
                trades
            )

            if not res:
                st.warning("Data belum cukup")
            else:
                st.metric("Median Balance", f"${res['median']:,.0f}")
                st.metric("Risk of Ruin", f"{res['risk_of_ruin']*100:.2f}%")

                fig = go.Figure()
                for curve in res["curves"][:30]:
                    fig.add_trace(go.Scatter(y=curve, mode="lines", opacity=0.3))
                st.plotly_chart(fig, use_container_width=True)
