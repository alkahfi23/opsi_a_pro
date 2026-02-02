# =====================================================
# OPSI A PRO — SIGNAL HISTORY ENGINE
# FINAL | STABLE | REGIME FREEZE
# =====================================================

import os
import pandas as pd
from datetime import datetime

from config import SIGNAL_LOG_FILE


# =====================================================
# INIT FILE
# =====================================================
COLUMNS = [
    "Time",
    "Symbol",
    "Phase",
    "Regime",              # 🔒 REGIME FREEZE (ENTRY)
    "Score",
    "Entry",
    "SL",                  # EXECUTION SL
    "SL_Invalidation",     # STRUCTURE SL (HTF)
    "TP1",
    "TP2",
    "Status",
    "Mode",
    "Direction",
    "PositionSize",
    "AutoLabel"
]


def _init_file():
    if not os.path.exists(SIGNAL_LOG_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# LOAD HISTORY
# =====================================================
def load_signal_history():
    _init_file()
    try:
        df = pd.read_csv(SIGNAL_LOG_FILE)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)

    return df


# =====================================================
# SAVE SIGNAL (FREEZE REGIME)
# =====================================================
def save_signal(signal: dict):
    """
    Save signal with frozen regime & structure SL
    """

    _init_file()
    df = load_signal_history()

    row = {
        "Time": signal.get("Time"),
        "Symbol": signal.get("Symbol"),
        "Phase": signal.get("Phase"),
        "Regime": signal.get("Regime"),          # 🔒 freeze
        "Score": signal.get("Score"),
        "Entry": signal.get("Entry"),
        "SL": signal.get("SL"),
        "SL_Invalidation": signal.get("SL_Invalidation"),
        "TP1": signal.get("TP1"),
        "TP2": signal.get("TP2"),
        "Status": "OPEN",
        "Mode": signal.get("Mode"),
        "Direction": signal.get("Direction"),
        "PositionSize": signal.get("PositionSize", 0),
        "AutoLabel": "WAIT"
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE SIGNALS
# =====================================================
def auto_close_signals():
    """
    Auto update status:
    - TP1 HIT
    - TP2 HIT
    - SL HIT

    ⚠️ Uses candle CLOSE logic
    """

    if not os.path.exists(SIGNAL_LOG_FILE):
        return

    df = pd.read_csv(SIGNAL_LOG_FILE)

    if df.empty:
        return

    changed = False

    for i, row in df.iterrows():
        if row["Status"] != "OPEN":
            continue

        entry = row["Entry"]
        sl = row["SL"]
        tp1 = row["TP1"]
        tp2 = row["TP2"]
        direction = row["Direction"]

        # ⚠️ price simulation placeholder
        # (real execution should be replaced by live price fetch)
        last_price = entry

        if direction == "LONG":
            if last_price <= sl:
                df.at[i, "Status"] = "SL HIT"
                changed = True
            elif last_price >= tp2:
                df.at[i, "Status"] = "TP2 HIT"
                changed = True
            elif last_price >= tp1:
                df.at[i, "Status"] = "TP1 HIT"
                changed = True

        elif direction == "SHORT":
            if last_price >= sl:
                df.at[i, "Status"] = "SL HIT"
                changed = True
            elif last_price <= tp2:
                df.at[i, "Status"] = "TP2 HIT"
                changed = True
            elif last_price <= tp1:
                df.at[i, "Status"] = "TP1 HIT"
                changed = True

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# MERGE HISTORY (RESTORE CSV)
# =====================================================
def merge_signal_history(upload_df: pd.DataFrame) -> int:
    """
    Merge uploaded CSV without duplicating signals
    Identity = Time + Symbol + Mode
    """

    _init_file()
    df = load_signal_history()

    key_cols = ["Time", "Symbol", "Mode"]
    existing_keys = set(
        tuple(row) for row in df[key_cols].values
    )

    added = 0
    rows = []

    for _, row in upload_df.iterrows():
        key = tuple(row.get(col) for col in key_cols)
        if key not in existing_keys:
            rows.append(row)
            added += 1

    if rows:
        df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
        df.to_csv(SIGNAL_LOG_FILE, index=False)

    return added
