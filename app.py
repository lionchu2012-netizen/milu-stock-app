import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload, timeout=5)

st.set_page_config(page_title="雲端看盤系統", layout="wide")
st.title("📈 雲端即時看盤系統")

stock_symbol = st.text_input("輸入股票代號 (例如 2330.TW)", "2330.TW")

st.sidebar.header("技術指標設定")
show_ma = st.sidebar.checkbox("顯示 MA", value=True)
ma_periods = st.sidebar.multiselect("MA 週期", [5,10,20,60,120,240], default=[5,10,20])
show_ema = st.sidebar.checkbox("顯示 EMA", value=True)
ema_periods = st.sidebar.multiselect("EMA 週期", [5,10,20,60,120,240], default=[5,10,20])

interval = st.selectbox("分時選擇", ["5m","15m","60m","120m","180m","240m"])

st.text("下載資料中...")
df = yf.download(stock_symbol, period="60d", interval=interval)

# ✅ 關鍵修正：攤平 MultiIndex
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df.reset_index(inplace=True)

st.write("🔎 資料欄位：", df.columns.tolist())
st.dataframe(df.head())

# 計算 MA / EMA
if show_ma:
    for p in ma_periods:
        df[f"MA{p}"] = df["Close"].rolling(p).mean()

if show_ema:
    for p in ema_periods:
        df[f"EMA{p}"] = df["Close"].ewm(span=p, adjust=False).mean()

# ====== 畫圖 ======
fig = go.Figure()

# 👉 K 棒（一定會出來）
fig.add_trace(go.Candlestick(
    x=df['Datetime'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='K棒'
))

# MA
if show_ma:
    for p in ma_periods:
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df[f"MA{p}"], mode='lines', name=f"MA{p}"))

# EMA
if show_ema:
    for p in ema_periods:
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df[f"EMA{p}"], mode='lines', name=f"EMA{p}"))

fig.update_layout(xaxis_rangeslider_visible=False, height=750)
st.plotly_chart(fig, use_container_width=True)

if st.button("發送 Telegram 測試訊息"):
    send_telegram_message(f"{stock_symbol} 看盤系統測試訊息 {datetime.now()}")
    st.success("Telegram 訊息已發送 ✅")
