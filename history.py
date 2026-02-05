# =====================================================
# OPSI A PRO — SIGNAL HISTORY ENGINE
# FINAL | STABLE | REGIME FREEZE + TELEGRAM + COOLDOWN
# =====================================================

import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from config import (
    SIGNAL_LOG_FILE,
    SIGNAL_COOLDOWN_MINUTES,
    COOLDOWN_BY_MODE
)

from exchange import get_okx, fetch_ohlcv
from telegram_bot import send_telegram_message, format_trade_update
from scoring import institutional_score
from regime import detect_market_regime


# =====================================================
# FILE STRUCTURE
# =====================================================
COLUMNS = [
    "TimeUTC",             # ⏱️ internal UTC time
    "TimeWIB",             # 🕒 display only
    "Symbol",
    "Phase",
    "Regime",              # 🔒 entry regime
    "CurrentRegime",
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
    "PositionSize",
    "AutoLabel",
    "Alerted"
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
# SYMBOL COOLDOWN CHECK
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

    last = df.sort_values("TimeUTC", ascending=False).iloc[0]

    # ⛔ masih OPEN → block
    if last["Status"] == "OPEN":
        return True

    try:
        last_time = datetime.fromisoformat(last["TimeUTC"])
    except Exception:
        return False

    cooldown_until = last_time + timedelta(
        minutes=SIGNAL_COOLDOWN_MINUTES
    )

    return datetime.now(timezone.utc) < cooldown_until


# =====================================================
# SAVE SIGNAL (ENTRY)
# =====================================================
def save_signal(signal: dict):
    _init_file()
    df = load_signal_history()

    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(
        timezone(timedelta(hours=7))
    )

    row = {
        "TimeUTC": now_utc.isoformat(),
        "TimeWIB": now_wib.strftime("%Y-%m-%d %H:%M WIB"),
        "Symbol": signal["Symbol"],
        "Phase": signal["Phase"],
        "Regime": signal["Regime"],
        "CurrentRegime": signal["Regime"],
        "RegimeShift": False,
        "Score": signal["Score"],
        "Entry": signal["Entry"],
        "SL": signal["SL"],
        "SL_Invalidation": signal["SL_Invalidation"],
        "TP1": signal["TP1"],
        "TP2": signal["TP2"],
        "Status": "OPEN",
        "Mode": signal["Mode"],
        "Direction": signal["Direction"],
        "PositionSize": signal.get("PositionSize", 0),
        "AutoLabel": "WAIT",
        "Alerted": ""
    }

    df.loc[len(df)] = row
    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE (TP / SL)
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
# REGIME FLIP MONITOR
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
                    f"🚨 *REGIME FLIP ALERT*\n\n"
                    f"Symbol : `{symbol}`\n"
                    f"From   : {row['Regime']}\n"
                    f"To     : {current_regime}\n\n"
                    f"⚠️ Position still OPEN"
                )

        except Exception:
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)

# =====================================================
# BOT PERFORMANCE METRICS
# =====================================================
def calculate_bot_rating():
    df = load_signal_history()
    if df.empty:
        return None

    closed = df[df["Status"].isin(["TP1 HIT", "TP2 HIT", "SL HIT"])]
    if len(closed) < 20:
        return {
            "valid": False,
            "trades": len(closed)
        }

    wins = closed[closed["Status"] != "SL HIT"]
    losses = closed[closed["Status"] == "SL HIT"]

    win_rate = len(wins) / len(closed)

    avg_win_r = 1.5     # asumsi TP1 scaling
    avg_loss_r = 1.0

    expectancy = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)

    # =========================
    # BOT RATING
    # =========================
    if expectancy >= 0.7 and win_rate >= 0.6:
        rating = "A+"
    elif expectancy >= 0.4:
        rating = "A"
    elif expectancy >= 0.2:
        rating = "B"
    else:
        rating = "C"

    return {
        "valid": True,
        "rating": rating,
        "win_rate": round(win_rate * 100, 2),
        "expectancy": round(expectancy, 2),
        "trades": len(closed)
    }

