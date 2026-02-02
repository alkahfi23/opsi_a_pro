# =====================================================
# OPSI A PRO — HISTORY & AUTO MANAGEMENT (FINAL)
# =====================================================

import os
import pandas as pd

from config import SIGNAL_LOG_FILE
from exchange import get_okx
from regime import detect_market_regime


# =====================================================
# LOAD & INIT CSV
# =====================================================
def load_signal_history():
    cols = [
        "Time",
        "Symbol",
        "Phase",
        "Regime",
        "Score",
        "Entry",
        "SL",
        "TP1",
        "TP2",
        "Status",
        "Mode",
        "Direction",
        "PositionSize",
        "AutoLabel"
    ]

    if not os.path.exists(SIGNAL_LOG_FILE):
        pd.DataFrame(columns=cols).to_csv(SIGNAL_LOG_FILE, index=False)

    df = pd.read_csv(SIGNAL_LOG_FILE)

    # auto-migrate missing columns
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df.to_csv(SIGNAL_LOG_FILE, index=False)
    return df

def update_current_regime(okx, df):
    """
    Update CurrentRegime & RegimeShift for OPEN signals only
    """
    if df.empty:
        return df

    for i, row in df.iterrows():
        if row["Status"] != "OPEN":
            continue

        symbol = row["Symbol"]

        try:
            df4h = fetch_ohlcv(symbol, ENTRY_TF, LIMIT_4H)
            df1d = fetch_ohlcv(symbol, DAILY_TF, LIMIT_1D)
        except Exception:
            continue

        score_dummy = {}  # regime pakai struktur & trend
        current_regime = detect_market_regime(df4h, df1d, score_dummy)

        df.at[i, "CurrentRegime"] = current_regime
        df.at[i, "RegimeShift"] = current_regime != row["Regime"]

    return df


# =====================================================
# SAVE SIGNAL (ANTI DUPLICATE)
# =====================================================
def save_signal(sig):
    df = load_signal_history()

    duplicate = (
        (df["Symbol"] == sig["Symbol"]) &
        (df["Status"] == "OPEN") &
        (df["Mode"] == sig["Mode"]) &
        (df["Direction"] == sig["Direction"])
    )

    if duplicate.any():
        return

    record = {
        "Time": sig.get("Time"),
        "Symbol": sig.get("Symbol"),
        "Phase": sig.get("Phase"),
        "Regime": sig.get("Regime"),
        "Score": sig.get("Score"),
        "Entry": sig.get("Entry"),
        "SL": sig.get("SL"),
        "TP1": sig.get("TP1"),
        "TP2": sig.get("TP2"),
        "Status": "OPEN",
        "Mode": sig.get("Mode"),
        "Direction": sig.get("Direction"),
        "PositionSize": sig.get("PositionSize", 0.0),
        "AutoLabel": "WAIT"
    }

    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE TP / SL
# =====================================================
def auto_close_signals():
    df = load_signal_history()
    okx = get_okx()
    changed = False

    for i, row in df.iterrows():
        if row["Status"] not in ["OPEN", "TP1 HIT"]:
            continue

        try:
            price = okx.fetch_ticker(row["Symbol"]).get("last")
            if price is None:
                continue

            entry = float(row["Entry"])
            sl = float(row["SL"])
            tp1 = float(row["TP1"])
            tp2 = float(row["TP2"])
            direction = row["Direction"]

            # ===== LONG =====
            if direction == "LONG":
                if price <= sl:
                    df.at[i, "Status"] = "SL HIT"
                    changed = True
                elif price >= tp2:
                    df.at[i, "Status"] = "TP2 HIT"
                    changed = True
                elif price >= tp1 and row["Status"] == "OPEN":
                    df.at[i, "Status"] = "TP1 HIT"
                    changed = True

            # ===== SHORT =====
            else:
                if price >= sl:
                    df.at[i, "Status"] = "SL HIT"
                    changed = True
                elif price <= tp2:
                    df.at[i, "Status"] = "TP2 HIT"
                    changed = True
                elif price <= tp1 and row["Status"] == "OPEN":
                    df.at[i, "Status"] = "TP1 HIT"
                    changed = True

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO LABEL (SPOT ONLY)
# =====================================================
def auto_label_signals():
    df = load_signal_history()
    okx = get_okx()
    changed = False

    for i, row in df.iterrows():
        if row["Mode"] != "SPOT":
            continue
        if row["Status"] != "OPEN":
            continue

        try:
            price = okx.fetch_ticker(row["Symbol"]).get("last")
            if price is None:
                continue

            entry = float(row["Entry"])
            sl = float(row["SL"])
            tp1 = float(row["TP1"])

            if price <= sl:
                df.at[i, "AutoLabel"] = "INVALIDATED"
                df.at[i, "Status"] = "CLOSED"
                changed = True
            elif abs(price - entry) / entry <= 0.003:
                df.at[i, "AutoLabel"] = "RETEST"
                changed = True
            elif price >= tp1 * 0.95:
                df.at[i, "AutoLabel"] = "NO REENTRY"
                changed = True
            elif price > entry:
                df.at[i, "AutoLabel"] = "HOLD"
                changed = True
            else:
                df.at[i, "AutoLabel"] = "WAIT"
                changed = True

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)

# =====================================================
# RESTORE / MERGE SIGNAL HISTORY FROM CSV
# =====================================================
def merge_signal_history(upload_df):
    """
    Merge uploaded CSV into signal_history.csv
    Anti-duplicate by Symbol + Time + Mode + Direction
    """

    history = load_signal_history()

    # pastikan semua kolom ada
    for col in history.columns:
        if col not in upload_df.columns:
            upload_df[col] = ""

    upload_df = upload_df[history.columns]

    # buat unique key
    history["_key"] = (
        history["Symbol"].astype(str) +
        history["Time"].astype(str) +
        history["Mode"].astype(str) +
        history["Direction"].astype(str)
    )

    upload_df["_key"] = (
        upload_df["Symbol"].astype(str) +
        upload_df["Time"].astype(str) +
        upload_df["Mode"].astype(str) +
        upload_df["Direction"].astype(str)
    )

    new_rows = upload_df[~upload_df["_key"].isin(history["_key"])]

    if len(new_rows) > 0:
        history = pd.concat(
            [history.drop(columns="_key"), new_rows.drop(columns="_key")],
            ignore_index=True
        )
        history.to_csv(SIGNAL_LOG_FILE, index=False)

    return len(new_rows)

