# =====================================================
# OPSI A PRO — SIGNAL HISTORY ENGINE
# FINAL | STABLE | REGIME FREEZE + TELEGRAM + COOLDOWN
# =====================================================

import os
import pandas as pd
from datetime import datetime, timedelta

from config import (
    SIGNAL_LOG_FILE,
    SIGNAL_COOLDOWN_MINUTES,
    COOLDOWN_BY_MODE
)

from exchange import get_okx, fetch_ohlcv
from telegram_bot import (
    send_telegram_message,
    format_trade_update
)
from scoring import institutional_score
from regime import detect_market_regime


# =====================================================
# FILE STRUCTURE
# =====================================================
COLUMNS = [
    "Time",
    "Symbol",
    "Phase",
    "Regime",              # 🔒 entry regime (freeze)
    "CurrentRegime",       # 🔄 live regime
    "RegimeShift",         # 🚨 flag
    "Score",
    "Entry",
    "SL",
    "SL_Invalidation",
    "TP1",
    "TP2",
    "Status",
    "Mode",
    "Direction",
    "PositionSize",
    "AutoLabel",
    "Alerted"              # ⛔ anti spam telegram
]


# =====================================================
# INIT FILE
# =====================================================
def _init_file():
    if not os.path.exists(SIGNAL_LOG_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(
            SIGNAL_LOG_FILE, index=False
        )


# =====================================================
# LOAD HISTORY
# =====================================================
def load_signal_history():
    _init_file()
    try:
        return pd.read_csv(SIGNAL_LOG_FILE)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


# =====================================================
# SYMBOL COOLDOWN CHECK (ANTI DUPLICATE)
# =====================================================
def is_symbol_in_cooldown(symbol: str, mode: str) -> bool:
    df = load_signal_history()
    if df.empty:
        return False

    df = df[df["Symbol"] == symbol]
    if COOLDOWN_BY_MODE:
        df = df[df["Mode"] == mode]

    if df.empty:
        return False

    last = df.sort_values("Time", ascending=False).iloc[0]

    # masih OPEN → BLOCK
    if last["Status"] == "OPEN":
        return True

    # cek waktu cooldown
    try:
        last_time = datetime.strptime(
            last["Time"], "%Y-%m-%d %H:%M WIB"
        )
    except Exception:
        return False

    cooldown_until = last_time + timedelta(
        minutes=SIGNAL_COOLDOWN_MINUTES
    )

    return datetime.now() < cooldown_until


# =====================================================
# SAVE SIGNAL (ENTRY SNAPSHOT)
# =====================================================
def save_signal(signal: dict):
    _init_file()
    df = load_signal_history()

    row = {
        "Time": signal.get("Time"),
        "Symbol": signal.get("Symbol"),
        "Phase": signal.get("Phase"),
        "Regime": signal.get("Regime"),          # 🔒 freeze
        "CurrentRegime": signal.get("Regime"),
        "RegimeShift": False,
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
        "AutoLabel": "WAIT",
        "Alerted": ""
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE (TP / SL) + TELEGRAM
# =====================================================
def auto_close_signals():
    if not os.path.exists(SIGNAL_LOG_FILE):
        return

    df = pd.read_csv(SIGNAL_LOG_FILE)
    if df.empty:
        return

    okx = get_okx()
    changed = False

    for i, row in df.iterrows():
        if row["Status"] not in ["OPEN", "TP1 HIT"]:
            continue

        try:
            price = okx.fetch_ticker(row["Symbol"])["last"]

            sl = float(row["SL"])
            tp1 = float(row["TP1"])
            tp2 = float(row["TP2"])
            direction = row["Direction"]

            new_status = None

            if direction == "LONG":
                if price <= sl:
                    new_status = "SL HIT"
                elif price >= tp2:
                    new_status = "TP2 HIT"
                elif price >= tp1 and row["Status"] == "OPEN":
                    new_status = "TP1 HIT"
            else:
                if price >= sl:
                    new_status = "SL HIT"
                elif price <= tp2:
                    new_status = "TP2 HIT"
                elif price <= tp1 and row["Status"] == "OPEN":
                    new_status = "TP1 HIT"

            if new_status and row["Alerted"] != new_status:
                df.at[i, "Status"] = new_status
                df.at[i, "Alerted"] = new_status
                changed = True

                send_telegram_message(
                    format_trade_update(df.loc[i].to_dict())
                )

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# REGIME FLIP MONITOR (OPEN ONLY)
# =====================================================
def monitor_regime_flip():
    if not os.path.exists(SIGNAL_LOG_FILE):
        return

    df = pd.read_csv(SIGNAL_LOG_FILE)
    if df.empty:
        return

    changed = False

    for i, row in df.iterrows():
        if row["Status"] != "OPEN":
            continue

        try:
            symbol = row["Symbol"]

            df4h = fetch_ohlcv(symbol, "4h", 200)
            df1d = fetch_ohlcv(symbol, "1d", 200)

            score_data = institutional_score(
                df4h, df1d, row["Direction"]
            )

            current_regime = detect_market_regime(
                df4h, df1d, score_data
            )

            df.at[i, "CurrentRegime"] = current_regime

            if (
                current_regime != row["Regime"]
                and not row["RegimeShift"]
            ):
                df.at[i, "RegimeShift"] = True
                changed = True

                send_telegram_message(
                    f"🚨 REGIME FLIP ALERT\n\n"
                    f"Symbol : {symbol}\n"
                    f"From   : {row['Regime']}\n"
                    f"To     : {current_regime}\n\n"
                    f"⚠️ Position still OPEN\n"
                    f"Consider risk reduction"
                )

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# MERGE HISTORY (CSV RESTORE)
# =====================================================
def merge_signal_history(upload_df: pd.DataFrame) -> int:
    _init_file()
    df = load_signal_history()

    key_cols = ["Time", "Symbol", "Mode"]
    existing = set(tuple(row) for row in df[key_cols].values)

    rows = []
    added = 0

    for _, row in upload_df.iterrows():
        key = tuple(row.get(col) for col in key_cols)
        if key not in existing:
            rows.append(row)
            added += 1

    if rows:
        df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
        df.to_csv(SIGNAL_LOG_FILE, index=False)

    return added
