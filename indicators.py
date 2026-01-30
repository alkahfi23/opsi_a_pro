# =====================================================
# OPSI A PRO — INDICATORS
# =====================================================
import pandas as pd
import numpy as np
from config import VO_FAST, VO_SLOW

def supertrend(df, period, mult):
    h,l,c = df.high, df.low, df.close
    tr = pd.concat([
        h-l,
        (h-c.shift()).abs(),
        (l-c.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(span=period, adjust=False).mean()
    hl2 = (h+l)/2
    upper = hl2 + mult*atr
    lower = hl2 - mult*atr

    trend = [1]
    stl = [lower.iloc[0]]

    for i in range(1, len(df)):
        if trend[i-1] == 1:
            stl.append(max(lower.iloc[i], stl[i-1]))
            trend.append(1 if c.iloc[i] > stl[i] else -1)
        else:
            stl.append(min(upper.iloc[i], stl[i-1]))
            trend.append(-1 if c.iloc[i] < stl[i] else 1)

    return pd.Series(stl), pd.Series(trend)

def volume_osc(volume):
    return (
        volume.ewm(VO_FAST).mean()
        - volume.ewm(VO_SLOW).mean()
    ) / volume.ewm(VO_SLOW).mean() * 100

def accumulation_distribution(df):
    h,l,c,v = df.high, df.low, df.close, df.volume
    mfm = ((c-l)-(h-c))/(h-l)
    mfm = mfm.replace([np.inf,-np.inf],0).fillna(0)
    return (mfm*v).cumsum()

def find_support(df, lb):
    levels=[]
    for i in range(lb, len(df)-lb):
        if df.low.iloc[i] == min(df.low.iloc[i-lb:i+lb+1]):
            levels.append(df.low.iloc[i])
    return sorted(set(levels))

def find_resistance(df, lb):
    levels=[]
    for i in range(lb, len(df)-lb):
        if df.high.iloc[i] == max(df.high.iloc[i-lb:i+lb+1]):
            levels.append(df.high.iloc[i])
    return sorted(set(levels))
