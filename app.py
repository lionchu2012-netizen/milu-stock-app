# app.py - Stable v1.4 (Auto Candlestick Fix)

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime
import os

st.set_page_config(page_title="雲端看盤系統", layout="wide")

st.title("📈 雲端即時看盤系統")
st.caption("Version: v1.4.0 - Auto K棒欄位修正")

# ===== Telegram =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram 尚未設定")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        st.error(f"Telegram 發送失敗: {e}")

# ===== UI =====
stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")

st.sidebar.header("技術指標設定")
show_ma = st.sidebar.checkbox("顯示 MA", value=True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", value=True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60,120,240], default=[5,10,20])

interval = st.selectbox("分時選擇", ["5m","15m","60m","120m","180m","240m"])

# ===== Download Data =====
st.info("📥 下載資料中...")
df = yf.download(stock_symbol, period="60d", interval=interval, auto_adjust=False)

if df.empty:
    st.error("⚠️ 查無資料")
    st.stop()

# 👉 把 index 變成欄位
df = df.reset_index()

# 👉 自動找時間欄位
time_col = None
for col in ["Datetime", "Date"]:
    if col in df.columns:
        time_col = col
        break

if not time_col:
    st.error(f"找不到時間欄位，實際欄位是：{df.columns.tolist()}")
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

# ✅ Candlestick 一定畫
fig.add_trace(go.Candlestick(
    x=df[time_col],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="K棒"
))

if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(x=df[time_col], y=df[f"MA{p}"], mode="lines", name=f"MA{p}"))

if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(x=df[time_col], y=df[f"EMA{p}"], mode="lines", name=f"EMA{p}"))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=700,
    margin=dict(l=30, r=30, t=40, b=30)
)

st.plotly_chart(fig, use_container_width=True)

# ===== Telegram Test =====
if st.button("📨 發送 Telegram 測試訊息"):
    send_telegram_message(f"{stock_symbol} 看盤系統測試 {datetime.now()}")
    st.success("Telegram 訊息已發送")
