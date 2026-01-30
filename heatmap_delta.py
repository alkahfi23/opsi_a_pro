# =====================================================
# OPSI A PRO — HEATMAP DELTA SCORE (ROTASI INSTITUSI)
# =====================================================
import os
import pandas as pd
from datetime import datetime

from exchange import fetch_ohlcv
from indicators import supertrend
from scoring import institutional_score
from regime import detect_market_regime
from config import ENTRY_TF, DAILY_TF, LIMIT_4H, LIMIT_1D

SNAPSHOT_FILE = "score_snapshot.csv"


def take_score_snapshot(okx, symbols):
    rows = []
    ts = datetime.utcnow().isoformat()

    for symbol in symbols:
        try:
            df4h = fetch_ohlcv(symbol, ENTRY_TF, LIMIT_4H)
            df1d = fetch_ohlcv(symbol, DAILY_TF, LIMIT_1D)

            if len(df4h) < 50 or len(df1d) < 50:
                continue

            _, trend = supertrend(df4h, period=10, mult=3.0)
            direction = "LONG" if trend.iloc[-1] == 1 else "SHORT"

            score_data = institutional_score(df4h, df1d, direction)
            score = score_data["TotalScore"]

            regime = detect_market_regime(df4h, df1d, score_data)

            rows.append({
                "Time": ts,
                "Symbol": symbol,
                "Direction": direction,
                "Score": score,
                "Regime": regime
            })

        except Exception:
            continue

    df_new = pd.DataFrame(rows)

    if os.path.exists(SNAPSHOT_FILE):
        df_old = pd.read_csv(SNAPSHOT_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(SNAPSHOT_FILE, index=False)
    return df_new

def compute_score_delta():
    if not os.path.exists(SNAPSHOT_FILE):
        return None

    df = pd.read_csv(SNAPSHOT_FILE)

    # ambil 2 snapshot terakhir per symbol
    df = df.sort_values("Time")

    last = df.groupby("Symbol").tail(2)

    delta_rows = []

    for symbol, g in last.groupby("Symbol"):
        if len(g) < 2:
            continue

        prev, curr = g.iloc[0], g.iloc[1]

        delta_rows.append({
            "Symbol": symbol,
            "Direction": curr["Direction"],
            "Score": curr["Score"],
            "Delta": curr["Score"] - prev["Score"],
            "Regime": curr["Regime"]
        })

    return pd.DataFrame(delta_rows)
