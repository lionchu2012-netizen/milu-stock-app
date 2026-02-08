# app.py - Stable Version for Render + Streamlit
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime
import os

# ====== App 版本資訊 ======
APP_VERSION = "v1.3.0 - Stable Render + K棒顯示修正版"
BUILD_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ====== Telegram (用 Render 環境變數) ======
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram 環境變數未設定")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Telegram 發送失敗: {e}")

# ====== Streamlit 設定 ======
st.set_page_config(page_title="雲端看盤系統", layout="wide")
st.title("📈 雲端即時看盤系統")
st.caption(f"🧾 Version: {APP_VERSION} ｜ ⏱ Build: {BUILD_TIME}")

# ====== 輸入 ======
stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW / AAPL)", "2330.TW")
interval = st.selectbox("K棒週期", ["5m","15m","60m","120m","1d"])

st.sidebar.header("技術指標")
show_ma = st.sidebar.checkbox("顯示 MA", True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60,120,240], [5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60,120,240], [5,10,20])
show_rsi = st.sidebar.checkbox("顯示 RSI", False)
show_kd = st.sidebar.checkbox("顯示 KD", False)

# ====== 下載資料 ======
st.info("📡 下載股票資料中...")
try:
    df = yf.download(stock_symbol, period="60d", interval=interval, progress=False)
    if df.empty:
        st.error("⚠️ 查無資料，請確認代號是否正確")
        st.stop()
    df.reset_index(inplace=True)
    st.success("資料下載完成 ✅")
except Exception as e:
    st.error(f"資料下載失敗: {e}")
    st.stop()

# ====== 技術指標 ======
if show_ma:
    for p in ma_periods:
        df[f"MA{p}"] = df["Close"].rolling(p).mean()

if show_ema:
    for p in ema_periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()

if show_rsi:
    delta = df["Close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    rs = up.rolling(14).mean() / down.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

if show_kd:
    low_min = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()
    df["K"] = 100 * (df["Close"] - low_min) / (high_max - low_min)
    df["D"] = df["K"].rolling(3).mean()

# ====== 畫圖 ======
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Datetime"] if "Datetime" in df else df["Date"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="K棒"
))

if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(
            x=df["Datetime"] if "Datetime" in df else df["Date"],
            y=df[f"MA{p}"],
            mode="lines",
            name=f"MA{p}"
        ))

if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(
            x=df["Datetime"] if "Datetime" in df else df["Date"],
            y=df[f"EMA{p}"],
            mode="lines",
            name=f"EMA{p}"
        ))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=700,
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# ====== Telegram 測試 ======
st.divider()
if st.button("📨 發送 Telegram 測試訊息"):
    send_telegram_message(f"{stock_symbol} 看盤系統測試訊息 {datetime.now()}")
    st.success("Telegram 訊息已送出（如果有設定環境變數）")
