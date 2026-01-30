# exchange.py
import ccxt
import pandas as pd
import streamlit as st

@st.cache_resource
def get_okx():
    ex = ccxt.okx({"enableRateLimit": True})
    ex.load_markets()
    return ex

@st.cache_data(ttl=300)
def fetch_ohlcv(symbol, tf, limit):
    okx = get_okx()   # ambil dari cache_resource
    return pd.DataFrame(
        okx.fetch_ohlcv(symbol, tf, limit=limit),
        columns=["t","open","high","low","close","volume"]
    )
