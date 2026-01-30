# =====================================================
# OPSI A PRO — HISTORY & AUTO MANAGEMENT
# =====================================================
import os
import pandas as pd
from config import SIGNAL_LOG_FILE
from exchange import fetch_ohlcv

def load_signal_history():
    cols = [
        "Time","Symbol","Phase","Score",
        "Entry","SL","TP1","TP2",
        "Status","Mode","Direction","PositionSize","AutoLabel"
    ]
    if not os.path.exists(SIGNAL_LOG_FILE):
        pd.DataFrame(columns=cols).to_csv(SIGNAL_LOG_FILE, index=False)

    df = pd.read_csv(SIGNAL_LOG_FILE)

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df.to_csv(SIGNAL_LOG_FILE, index=False)
    return df


def save_signal(sig):
    df = load_signal_history()

    dup = (
        (df["Symbol"] == sig["Symbol"]) &
        (df["Status"] == "OPEN") &
        (df["Mode"] == sig["Mode"]) &
        (df["Direction"] == sig["Direction"])
    )

    if dup.any():
        return

    sig["Status"] = "OPEN"
    sig["AutoLabel"] = "WAIT"

    df = pd.concat([df, pd.DataFrame([sig])], ignore_index=True)
    df.to_csv(SIGNAL_LOG_FILE, index=False)


def auto_close_signals(okx):
    df = load_signal_history()
    changed = False

    for i,row in df.iterrows():
        if row["Status"] not in ["OPEN","TP1 HIT"]:
            continue

        try:
            price = okx.fetch_ticker(row["Symbol"])["last"]
            entry, sl, tp1, tp2 = row["Entry"], row["SL"], row["TP1"], row["TP2"]
            direction = row["Direction"]

            if direction == "LONG":
                if price <= sl:
                    df.at[i,"Status"] = "SL HIT"
                elif price >= tp2:
                    df.at[i,"Status"] = "TP2 HIT"
                elif price >= tp1:
                    df.at[i,"Status"] = "TP1 HIT"

            else:
                if price >= sl:
                    df.at[i,"Status"] = "SL HIT"
                elif price <= tp2:
                    df.at[i,"Status"] = "TP2 HIT"
                elif price <= tp1:
                    df.at[i,"Status"] = "TP1 HIT"

            changed = True
        except:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)
