# =====================================================
# OPSI A PRO — SIGNAL HISTORY ENGINE
# FINAL | STABLE | REGIME FREEZE + TELEGRAM ALERT
# =====================================================

import os
import pandas as pd

from config import SIGNAL_LOG_FILE
from exchange import get_okx
from telegram_bot import send_telegram_message, format_trade_update


# =====================================================
# FILE STRUCTURE
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
    "AutoLabel",
    "CurrentRegime",     # 🔄 live regime
    "RegimeShift",       # 🚨 flag
    "Alerted"              # ⛔ anti spam telegram
]


# =====================================================
# INIT FILE
# =====================================================
def _init_file():
    if not os.path.exists(SIGNAL_LOG_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(SIGNAL_LOG_FILE, index=False)


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
# SAVE SIGNAL (ENTRY)
# =====================================================
def save_signal(signal: dict):
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
        "AutoLabel": "WAIT",
        "Alerted": ""
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE SIGNALS (REAL PRICE + TELEGRAM)
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

            entry = float(row["Entry"])
            sl = float(row["SL"])
            tp1 = float(row["TP1"])
            tp2 = float(row["TP2"])
            direction = row["Direction"]

            prev_status = row["Status"]
            new_status = None

            if direction == "LONG":
                if price <= sl:
                    new_status = "SL HIT"
                elif price >= tp2:
                    new_status = "TP2 HIT"
                elif price >= tp1 and prev_status == "OPEN":
                    new_status = "TP1 HIT"

            else:  # SHORT
                if price >= sl:
                    new_status = "SL HIT"
                elif price <= tp2:
                    new_status = "TP2 HIT"
                elif price <= tp1 and prev_status == "OPEN":
                    new_status = "TP1 HIT"

            if new_status and row.get("Alerted") != new_status:
                df.at[i, "Status"] = new_status
                df.at[i, "Alerted"] = new_status
                changed = True

                # 📩 TELEGRAM ALERT
                try:
                    msg = format_trade_update(df.loc[i].to_dict())
                    send_telegram_message(msg)
                except Exception as e:
                    print("Telegram error:", e)

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# MERGE HISTORY (RESTORE CSV)
# =====================================================
def merge_signal_history(upload_df: pd.DataFrame) -> int:
    _init_file()
    df = load_signal_history()

    key_cols = ["Time", "Symbol", "Mode"]
    existing_keys = set(tuple(row) for row in df[key_cols].values)

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


# =====================================================
# REGIME FLIP ALERT (NON-DESTRUCTIVE)
# =====================================================
def monitor_regime_flip():
    """
    Check regime change for OPEN positions
    Send telegram alert if regime flips
    """

    from exchange import get_okx
    from indicators import accumulation_distribution
    from scoring import institutional_score
    from regime import detect_market_regime
    from telegram_bot import send_telegram_message

    if not os.path.exists(SIGNAL_LOG_FILE):
        return

    df = pd.read_csv(SIGNAL_LOG_FILE)
    if df.empty:
        return

    okx = get_okx()
    changed = False

    for i, row in df.iterrows():
        if row["Status"] != "OPEN":
            continue

        try:
            symbol = row["Symbol"]
            entry_regime = row["Regime"]

            # ===== fetch fresh data =====
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
                current_regime != entry_regime
                and not row.get("RegimeShift", False)
            ):
                df.at[i, "RegimeShift"] = True
                changed = True

                # 📩 TELEGRAM ALERT
                msg = (
                    f"🚨 REGIME FLIP ALERT\n\n"
                    f"Symbol : {symbol}\n"
                    f"From   : {entry_regime}\n"
                    f"To     : {current_regime}\n\n"
                    f"⚠️ Position still OPEN\n"
                    f"Consider risk reduction"
                )

                send_telegram_message(msg)

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)


    return added
