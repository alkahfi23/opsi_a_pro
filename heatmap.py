# =====================================================
# OPSI A PRO — SCORE HEATMAP
# =====================================================
import pandas as pd
import plotly.express as px

from exchange import fetch_ohlcv
from indicators import supertrend
from scoring import institutional_score
from regime import detect_market_regime
from config import ENTRY_TF, DAILY_TF, LIMIT_4H, LIMIT_1D


def generate_score_heatmap(okx, symbols):
    rows = []

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
                "Symbol": symbol,
                "Direction": direction,
                "Score": score,
                "Regime": regime
            })

        except Exception:
            continue

    return pd.DataFrame(rows)
