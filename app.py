# app.py - Debug Stable v1.5 (Force Candlestick)

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="雲端看盤系統", layout="wide")
st.title("📈 雲端即時看盤系統")
st.caption("Version: v1.5.0 - Force Candlestick Debug")

# ===== UI =====
stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")
interval = st.selectbox("分時選擇", ["5m","15m","60m","120m","180m","240m"])

st.sidebar.header("技術指標")
show_ma = st.sidebar.checkbox("顯示 MA", value=True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60], default=[5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", value=True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60], default=[5,10,20])

# ===== Download =====
st.info("📥 下載資料中...")
df = yf.download(stock_symbol, period="60d", interval=interval, auto_adjust=False)

if df.empty:
    st.error("⚠️ 查無資料")
    st.stop()

df = df.reset_index()

# 🔎 Debug：顯示欄位
st.write("🔎 資料欄位：", df.columns.tolist())
st.write("🔎 前 5 筆資料：")
st.dataframe(df.head())

# 自動找時間欄位
time_col = None
for col in ["Datetime", "Date"]:
    if col in df.columns:
        time_col = col
        break

if not time_col:
    st.error(f"找不到時間欄位：{df.columns.tolist()}")
    st.stop()

# ===== Indicators =====
if show_ma:
    for p in ma_periods:
        df[f"MA{p}"] = df["Close"].rolling(p).mean()

if show_ema:
    for p in ema_periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()

# ===== Plot =====
fig = go.Figure()

# 🔥 強制先畫 K 棒（底層）
fig.add_trace(go.Candlestick(
    x=df[time_col],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="K棒",
    increasing_line_color="red",
    decreasing_line_color="green"
))

# 再畫線（上層）
if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[f"MA{p}"],
            mode="lines",
            name=f"MA{p}"
        ))

if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[f"EMA{p}"],
            mode="lines",
            name=f"EMA{p}"
        ))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=750,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
