# =====================================================
# OPSI A PRO — MAIN APP
# FINAL | STABLE | INSTITUTIONAL GRADE | STREAMLIT SAFE
# =====================================================

import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from exchange import get_okx
from utils import (
    is_danger_time,
    is_safe_spot_time,
    is_safe_futures_time,
    wib_hour
)

from config import (
    RATE_LIMIT_DELAY,
    MAX_SCAN_SYMBOLS,
    FUTURES_BIG_COINS
)

from signals import check_signal
from history import (
    load_signal_history,
    save_signal,
    auto_close_signals,
    merge_signal_history,
    monitor_regime_flip
)

from montecarlo import run_monte_carlo
from analyze_single_coin import analyze_single_coin
from telegram_bot import send_telegram_message, format_signal_message


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="OPSI A PRO — Institutional Grade",
    layout="wide"
)

st.title("🚀 OPSI A PRO — SPOT & FUTURES (Institutional Grade)")


# =====================================================
# INIT EXCHANGE
# =====================================================
okx = get_okx()


# =====================================================
# AUTO MAINTENANCE (SAFE FOR STREAMLIT CLOUD)
# =====================================================
try:
    auto_close_signals()     # TP / SL check + telegram
    monitor_regime_flip()    # regime flip alert
except Exception:
    pass


# =====================================================
# MODE & BALANCE
# =====================================================
MODE = st.radio(
    "🧭 Trading Mode",
    ["SPOT", "FUTURES"],
    horizontal=True
)

BALANCE = st.number_input(
    "💰 Account Balance (USDT)",
    value=10000.0,
    step=100.0
)

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📡 Scan Market",
    "📜 Signal History",
    "🎲 Monte Carlo",
    "🎯 Analisa Single Coin",
    "🔥 Score Heatmap",
    "🔄 Δ Score (Rotation)"
])


# =====================================================
# TAB 1 — SCAN MARKET
# =====================================================
with tab1:
    if st.button("🔍 Scan Market"):

        # =========================
        # SYMBOL UNIVERSE
        # =========================
        if MODE == "FUTURES":
            symbols = FUTURES_BIG_COINS
        else:
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

            try:
                sig = check_signal(symbol, MODE, BALANCE)
            except Exception:
                continue

            if sig and sig.get("SignalType") == "TRADE_EXECUTION":

                # prevent duplicate telegram
                before = len(load_signal_history())

                save_signal(sig)
                after = len(load_signal_history())

                if after > before:
                    found.append(sig)

                    # =========================
                    # TELEGRAM ALERT (ENTRY)
                    # =========================
                    try:
                        msg = format_signal_message(sig)
                        send_telegram_message(msg)
                        st.toast("📩 Telegram sent", icon="📨")
                    except Exception as e:
                        st.warning(f"Telegram error: {e}")

            progress.progress(i / total)
            time.sleep(RATE_LIMIT_DELAY)

        if found:
            st.success(f"🔥 Found {len(found)} A+ setups")
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Tidak ada setup A+ ditemukan")


# =====================================================
# TAB 2 — SIGNAL HISTORY
# =====================================================
with tab2:
    st.subheader("📜 Signal History")

    df = load_signal_history()

    st.metric("Total Signals", len(df))
    st.metric("OPEN Signals", (df["Status"] == "OPEN").sum())

    preferred_cols = [
        "Time",
        "Symbol",
        "Phase",
        "Regime",          # frozen
        "CurrentRegime",   # live
        "RegimeShift",
        "Score",
        "Entry",
        "SL",
        "SL_Invalidation",
        "TP1",
        "TP2",
        "Status",
        "Mode",
        "Direction",
        "PositionSize"
    ]

    show_cols = [c for c in preferred_cols if c in df.columns]

    st.dataframe(
        df[show_cols].sort_values("Time", ascending=False),
        use_container_width=True
    )

    st.divider()

    # =========================
    # RESTORE CSV
    # =========================
    st.subheader("📤 Restore Riwayat dari CSV")

    uploaded = st.file_uploader(
        "Upload file signal_history.csv lama",
        type=["csv"]
    )

    if uploaded:
        upload_df = pd.read_csv(uploaded)
        st.dataframe(upload_df.head(), use_container_width=True)

        if st.button("♻️ Merge ke History"):
            added = merge_signal_history(upload_df)

            if added > 0:
                st.success(f"✅ {added} signal baru ditambahkan")
            else:
                st.info("ℹ️ Tidak ada signal baru")

            st.experimental_rerun()

    st.download_button(
        "⬇️ Download Full History",
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

            if res:
                st.metric("Median Balance", f"${res['median']:,.0f}")
                st.metric(
                    "Risk of Ruin",
                    f"{res['risk_of_ruin'] * 100:.2f}%"
                )

                fig = go.Figure()
                for curve in res["curves"][:30]:
                    fig.add_trace(go.Scatter(
                        y=curve,
                        mode="lines",
                        opacity=0.3
                    ))

                st.plotly_chart(fig, use_container_width=True)


# =====================================================
# TAB 4 — ANALISA SINGLE COIN
# =====================================================
with tab4:
    st.subheader("🎯 Analisa Single Coin")

    symbols = FUTURES_BIG_COINS if MODE == "FUTURES" else [
        s for s, m in okx.markets.items()
        if m.get("spot") and m.get("active") and s.endswith("/USDT")
    ]

    col1, col2 = st.columns(2)
    with col1:
        symbol = st.selectbox("Pilih Coin", symbols)
    with col2:
        mode_an = st.radio(
            "Mode Analisa",
            ["SPOT", "FUTURES"],
            horizontal=True
        )

    bal_an = st.number_input(
        "Balance untuk Analisa (USDT)",
        value=10000.0,
        step=100.0
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
            for r in res["Reasons"]:
                st.write(f"• {r}")
        else:
            st.success("✅ SETUP VALID")
            st.json({
                "Entry": res["Entry"],
                "SL": res["SL"],
                "TP1": res["TP1"],
                "TP2": res["TP2"],
                "Position Size": res["PositionSize"]
            })


# =====================================================
# TAB 5 — SCORE HEATMAP
# =====================================================
with tab5:
    st.subheader("🔥 Institutional Score Heatmap")
    from heatmap import generate_score_heatmap

    symbols = FUTURES_BIG_COINS if MODE == "FUTURES" else [
        s for s, m in okx.markets.items()
        if m.get("spot") and m.get("active") and s.endswith("/USDT")
    ][:60]

    if st.button("🎨 Generate Heatmap"):
        df_hm = generate_score_heatmap(okx, symbols)

        if not df_hm.empty:
            st.dataframe(df_hm, use_container_width=True)

            fig = px.imshow(
                df_hm.set_index("Symbol")[["Score"]],
                aspect="auto",
                title="Institutional Score Heatmap"
            )
            st.plotly_chart(fig, use_container_width=True)


# =====================================================
# TAB 6 — Δ SCORE ROTATION
# =====================================================
with tab6:
    st.subheader("🔄 Institutional Rotation (Δ Score)")
    from heatmap_delta import take_score_snapshot, compute_score_delta

    symbols = FUTURES_BIG_COINS if MODE == "FUTURES" else [
        s for s, m in okx.markets.items()
        if m.get("spot") and m.get("active") and s.endswith("/USDT")
    ][:60]

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📸 Take Snapshot"):
            take_score_snapshot(okx, symbols)
            st.success("Snapshot saved")

    with col2:
        if st.button("🔥 Show Rotation"):
            df_delta = compute_score_delta()

            if df_delta is None or df_delta.empty:
                st.warning("Belum cukup snapshot")
            else:
                st.dataframe(df_delta, use_container_width=True)

                fig = px.imshow(
                    df_delta.set_index("Symbol")[["Delta"]],
                    aspect="auto",
                    title="Δ Institutional Score (Rotation)"
                )
                st.plotly_chart(fig, use_container_width=True)
