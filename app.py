# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import requests
import os

# =======================
# Telegram 設定
# =======================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram Token 或 Chat ID 尚未設定")
        return
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

# 股票代號輸入
stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")

# 技術分析選項
st.sidebar.header("技術指標設定")
show_ma = st.sidebar.checkbox("顯示 MA", True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_rsi = st.sidebar.checkbox("顯示 RSI", True)
show_kd = st.sidebar.checkbox("顯示 KD", True)

# 分時選擇
interval = st.selectbox("分時選擇", ["5m","15m","60m","120m","180m","240m"], index=2)

# =======================
# 下載資料
# =======================
data_load_state = st.text("下載資料中...")
try:
    df = yf.download(stock_symbol, period="60d", interval=interval)
    df.reset_index(inplace=True)
    # 確認欄位順序
    df = df[['Datetime','Open','High','Low','Close','Volume']]
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
# 畫圖（TradingView/XQ 風格）
# =======================
fig = go.Figure()

# K棒
fig.add_trace(go.Candlestick(
    x=df['Datetime'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    increasing_line_color='green',
    decreasing_line_color='red',
    name='K棒'
))

# MA/EMA
if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(
            x=df['Datetime'],
            y=df[f"MA{p}"],
            mode='lines',
            name=f"MA{p}",
            line=dict(width=1)
        ))

if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(
            x=df['Datetime'],
            y=df[f"EMA{p}"],
            mode='lines',
            name=f"EMA{p}",
            line=dict(width=1, dash='dot')
        ))

# 圖表配置
fig.update_layout(
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    height=700,
    margin=dict(l=10,r=10,t=50,b=10)
)

st.plotly_chart(fig, use_container_width=True)

# =======================
# 副圖：RSI / KD
# =======================
if show_rsi or show_kd:
    fig2 = go.Figure()
    if show_rsi:
        fig2.add_trace(go.Scatter(x=df['Datetime'], y=df['RSI'], name='RSI', line=dict(color='orange')))
    if show_kd:
        fig2.add_trace(go.Scatter(x=df['Datetime'], y=df['K'], name='K', line=dict(color='blue')))
        fig2.add_trace(go.Scatter(x=df['Datetime'], y=df['D'], name='D', line=dict(color='purple')))
    fig2.update_layout(template="plotly_dark", height=250, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)

# =======================
# Telegram 測試按鈕
# =======================
if st.button("發送 Telegram 測試訊息"):
    send_telegram_message(f"{stock_symbol} 看盤系統測試訊息 {datetime.now()}")
    st.success("Telegram 訊息已發送 ✅")
