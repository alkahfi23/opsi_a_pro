# =====================================================
# OPSI A PRO — MAIN APP (FINAL + SINGLE COIN)
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
from history import (
    load_signal_history,
    save_signal,
    auto_close_signals,
    auto_label_signals
)
from montecarlo import run_monte_carlo
from analyze_single_coin import analyze_single_coin   # 👈 SINGLE COIN
from history import merge_signal_history

# =====================================================
# PAGE
# =====================================================
st.set_page_config("OPSI A PRO — MODULAR", layout="wide")
st.title("🚀 OPSI A PRO — SPOT & FUTURES (Institutional)")

# =====================================================
# INIT
# =====================================================
okx = get_okx()

# auto maintenance
auto_close_signals()
auto_label_signals()

MODE = st.radio("🧭 Trading Mode", ["SPOT", "FUTURES"], horizontal=True)
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Scan Market",
    "📜 Signal History",
    "🎲 Monte Carlo",
    "🎯 Analisa Single Coin"
])

# =====================================================
# TAB 1 — SCAN MARKET
# =====================================================
with tab1:
    if st.button("🔍 Scan Market"):
        symbols = [
            s for s, m in okx.markets.items()
            if m.get("spot") and m.get("active") and s.endswith("/USDT")
        ][:MAX_SCAN_SYMBOLS]

        found = []
        progress = st.progress(0.0)
        status = st.empty()
        total = len(symbols)

        for i, symbol in enumerate(symbols, 1):
            status.info(f"Scanning {symbol} ({i}/{total})")

            sig = check_signal(symbol, MODE, BALANCE)

            if sig and sig.get("SignalType") == "TRADE_EXECUTION":
                save_signal(sig)
                found.append(sig)

            progress.progress(i / total)
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
    st.subheader("📜 Signal History")

    df = load_signal_history()

    st.metric("Total Signals", len(df))
    st.metric("OPEN Signals", (df["Status"] == "OPEN").sum())

    st.dataframe(
        df.sort_values("Time", ascending=False),
        use_container_width=True
    )

    st.divider()

    # =========================
    # 📤 RESTORE / IMPORT CSV
    # =========================
    st.subheader("📤 Restore Riwayat dari CSV")

    uploaded = st.file_uploader(
        "Upload file signal_history.csv lama",
        type=["csv"]
    )

    if uploaded:
        try:
            upload_df = pd.read_csv(uploaded)

            st.markdown("**Preview file:**")
            st.dataframe(upload_df.head(), use_container_width=True)

            if st.button("♻️ Merge ke History"):
                added = merge_signal_history(upload_df)

                if added > 0:
                    st.success(f"✅ Restore berhasil: {added} signal baru ditambahkan")
                else:
                    st.info("ℹ️ Tidak ada signal baru (semua sudah ada)")

                st.experimental_rerun()

        except Exception as e:
            st.error(f"❌ Gagal membaca CSV: {e}")

    st.divider()

    # =========================
    # 📥 DOWNLOAD BACKUP
    # =========================
    st.download_button(
        "⬇️ Download Full Signal History",
        df.to_csv(index=False),
        "signal_history_backup.csv",
        mime="text/csv"
    )

# =====================================================
# TAB 3 — MONTE CARLO
# =====================================================
with tab3:
    try:
        trade_results = pd.read_csv("trade_results.csv")
    except Exception:
        trade_results = pd.DataFrame()

    if trade_results.empty:
        st.warning("Trade result belum cukup")
    else:
        risk = st.slider("Risk / Trade (%)", 0.2, 3.0, 1.0) / 100
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
                st.metric(
                    "Median Balance",
                    f"${res['median']:,.0f}"
                )
                st.metric(
                    "Risk of Ruin",
                    f"{res['risk_of_ruin'] * 100:.2f}%"
                )

                fig = go.Figure()
                for curve in res["curves"][:30]:
                    fig.add_trace(
                        go.Scatter(
                            y=curve,
                            mode="lines",
                            opacity=0.3
                        )
                    )
                st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 4 — ANALISA SINGLE COIN
# =====================================================
with tab4:
    st.subheader("🎯 Analisa Single Coin (Logic Sama dengan Scanner)")

    symbols = [
        s for s, m in okx.markets.items()
        if m.get("spot") and m.get("active") and s.endswith("/USDT")
    ]

    col1, col2 = st.columns(2)
    with col1:
        symbol = st.selectbox("Pilih Coin", symbols)
    with col2:
        mode_an = st.radio("Mode Analisa", ["SPOT", "FUTURES"], horizontal=True)

    bal_an = st.number_input(
        "Balance untuk Analisa (USDT)",
        value=10000.0,
        step=100.0,
        key="bal_an"
    )

    if st.button("🔍 Analyze Coin"):
        res = analyze_single_coin(symbol, mode_an, bal_an)

        st.markdown(f"## 📊 Hasil Analisa — `{symbol}`")

        c1, c2, c3 = st.columns(3)
        c1.metric("Trend", res["Trend"])
        c2.metric("Score", res["Score"])
        c3.metric("Mode", mode_an)

        if res["Reasons"]:
            st.error("❌ NO TRADE")
            st.markdown("### 🔎 Alasan:")
            for r in res["Reasons"]:
                st.write(f"• {r}")
        else:
            st.success(f"✅ SETUP VALID ({res['Trend']})")
            st.markdown("### 📌 Level Trade")
            st.json({
                "Entry": res["Entry"],
                "SL": res["SL"],
                "TP1": res["TP1"],
                "TP2": res["TP2"],
                "Position Size": res["PositionSize"]
            })
