# =====================================================
# OPSI A PRO — SIGNAL HISTORY ENGINE
# REGIME FREEZE + TELEGRAM + COOLDOWN + BOT RATING
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


COLUMNS = [
    "TimeUTC",
    "TimeWIB",
    "Symbol",
    "Phase",
    "Regime",
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


def _init_file():
    if not os.path.exists(SIGNAL_LOG_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(
            SIGNAL_LOG_FILE, index=False
        )


def load_signal_history():
    _init_file()
    return pd.read_csv(SIGNAL_LOG_FILE)


# =====================================================
# COOLDOWN CHECK
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

    if last["Status"] == "OPEN":
        return True

    last_time = datetime.fromisoformat(last["TimeUTC"])
    cooldown_until = last_time + timedelta(
        minutes=SIGNAL_COOLDOWN_MINUTES
    )

    return datetime.now(timezone.utc) < cooldown_until


# =====================================================
# SAVE SIGNAL
# =====================================================
def save_signal(signal: dict):
    _init_file()
    df = load_signal_history()

    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(
        timezone(timedelta(hours=7))
    )

    df.loc[len(df)] = {
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

    df.to_csv(SIGNAL_LOG_FILE, index=False)


# =====================================================
# AUTO CLOSE + TELEGRAM
# =====================================================
def auto_close_signals():
    if not os.path.exists(SIGNAL_LOG_FILE):
        return

    df = pd.read_csv(SIGNAL_LOG_FILE)
    if df.empty:
        return

    okx = get_okx()
    changed = False

    for i in range(len(df)):
        status = df.at[i, "Status"]

        if status not in ["OPEN", "TP1 HIT"]:
            continue

        try:
            symbol = df.at[i, "Symbol"]
            direction = df.at[i, "Direction"]

            price = okx.fetch_ticker(symbol)["last"]

            sl  = float(df.at[i, "SL"])
            tp1 = float(df.at[i, "TP1"])
            tp2 = float(df.at[i, "TP2"])

            new_status = None

            if direction == "LONG":
                if price <= sl:
                    new_status = "SL HIT"
                elif price >= tp2:
                    new_status = "TP2 HIT"
                elif price >= tp1 and status == "OPEN":
                    new_status = "TP1 HIT"
            else:
                if price >= sl:
                    new_status = "SL HIT"
                elif price <= tp2:
                    new_status = "TP2 HIT"
                elif price <= tp1 and status == "OPEN":
                    new_status = "TP1 HIT"

            # ✅ SAFE CHECK (DATAFRAME BASED)
            if new_status and df.at[i, "Alerted"] != new_status:
                df.at[i, "Status"] = new_status
                df.at[i, "Alerted"] = new_status
                changed = True

                send_telegram_message(
                    format_trade_update(df.loc[i].to_dict())
                )

        except Exception as e:
            print(f"[AUTO CLOSE ERROR] {symbol}: {e}", flush=True)
            continue

    if changed:
        df.to_csv(SIGNAL_LOG_FILE, index=False)



# =====================================================
# BOT PERFORMANCE RATING
# =====================================================
def calculate_bot_rating():
    df = load_signal_history()
    closed = df[df["Status"].isin(
        ["TP1 HIT", "TP2 HIT", "SL HIT"]
    )]

    if len(closed) < 20:
        return {"valid": False, "trades": len(closed)}

    wins = closed[closed["Status"] != "SL HIT"]
    losses = closed[closed["Status"] == "SL HIT"]

    win_rate = len(wins) / len(closed)
    expectancy = (win_rate * 1.5) - ((1 - win_rate) * 1.0)

    if expectancy >= 0.7:
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

# =====================================================
# RATING SEND GUARD (ANTI SPAM)
# =====================================================
def should_send_rating() -> bool:
    """
    Kirim rating hanya setiap kelipatan 10 closed trades
    Minimal 20 trades agar valid
    """
    df = load_signal_history()
    if df.empty:
        return False

    closed = df[df["Status"].isin(["TP1 HIT", "TP2 HIT", "SL HIT"])]

    if len(closed) < 20:
        return False

    return len(closed) % 10 == 0
