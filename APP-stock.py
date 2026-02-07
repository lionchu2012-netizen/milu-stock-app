# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime

# =======================
# Telegram 設定
# =======================
TELEGRAM_BOT_TOKEN = "8429706030:AAFIs0VAPMFYwJTe9JRj9cIvEbELleXe7gw"
TELEGRAM_CHAT_ID = " t.me/milu_tool_bot"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram 發送失敗:", e)

# =======================
# Streamlit App
# =======================
st.set_page_config(page_title="雲端看盤系統", layout="wide")

st.title("📈 雲端即時看盤系統")

# 自選股輸入
stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")

# 技術分析選項
st.sidebar.header("技術指標設定")
show_ma = st.sidebar.checkbox("顯示 MA", value=True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", value=True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_rsi = st.sidebar.checkbox("顯示 RSI", value=True)
show_kd = st.sidebar.checkbox("顯示 KD", value=True)

# 分時選擇
interval = st.selectbox("分時選擇", ["5m","15m","60m","120m","180m","240m"])

# =======================
# 下載股票資料
# =======================
data_load_state = st.text("下載資料中...")
try:
    df = yf.download(stock_symbol, period="60d", interval=interval)
    df.reset_index(inplace=True)
    data_load_state.text("資料下載完成 ✅")
except Exception as e:
    st.error(f"資料下載失敗: {e}")
    st.stop()

# =======================
# 計算技術指標
# =======================
if show_ma:
    for p in ma_periods:
        df[f"MA{p}"] = df["Close"].rolling(p).mean()
if show_ema:
    for p in ema_periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()
if show_rsi:
    delta = df["Close"].diff()
    up, down = delta.clip(lower=0), -1*delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    df["RSI"] = 100 - 100 / (1 + roll_up / roll_down)
if show_kd:
    low_min = df['Low'].rolling(14).min()
    high_max = df['High'].rolling(14).max()
    df['K'] = 100*(df['Close'] - low_min)/(high_max - low_min)
    df['D'] = df['K'].rolling(3).mean()

# =======================
# 畫圖
# =======================
fig = go.Figure()

# K棒
fig.add_trace(go.Candlestick(x=df['Datetime'],
                             open=df['Open'],
                             high=df['High'],
                             low=df['Low'],
                             close=df['Close'],
                             name='K棒'))

# MA
if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df[f"MA{p}"], mode='lines', name=f"MA{p}"))

# EMA
if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df[f"EMA{p}"], mode='lines', name=f"EMA{p}"))

# RSI / KD 顯示在副圖
fig.update_layout(xaxis_rangeslider_visible=False, height=700)
st.plotly_chart(fig, use_container_width=True)

# =======================
# Telegram 推播示範
# =======================
if st.button("發送 Telegram 測試訊息"):
    send_telegram_message(f"{stock_symbol} 看盤系統測試訊息 {datetime.now()}")
    st.success("Telegram 訊息已發送 ✅")
