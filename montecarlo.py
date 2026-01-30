# =====================================================
# OPSI A PRO — MONTE CARLO
# =====================================================
import numpy as np
import pandas as pd

def run_monte_carlo(trade_results_df, signal_df, risk_pct, trades, runs=500):
    """
    trade_results_df: dataframe with column ["Symbol","R"]
    signal_df: signal history
    """

    # hanya SPOT + fase akumulasi
    mc = trade_results_df.merge(
        signal_df[["Symbol","Phase","Mode"]],
        on="Symbol",
        how="left"
    )

    mc = mc[
        (mc["Mode"] == "SPOT") &
        (mc["Phase"].str.contains("AKUMULASI", na=False))
    ]

    if len(mc) < 10:
        return None

    r_values = mc["R"].values
    curves = []

    for _ in range(runs):
        balance = 10000
        equity = [balance]

        for _ in range(trades):
            r = np.random.choice(r_values)
            balance += balance * risk_pct * r
            equity.append(balance)

        curves.append(equity)

    curves = np.array(curves)

    return {
        "curves": curves,
        "median": np.median(curves[:,-1]),
        "risk_of_ruin": (curves[:,-1] < 5000).mean()
    }
