# app.py  (TradingView / XQ 風格完整版穩定版)
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock K Chart", layout="wide")

st.title("📈 專業看盤 K 棒（TradingView / XQ 風格）")

# === Sidebar ===
with st.sidebar:
    st.header("設定")
    symbol = st.text_input("股票代碼", value="2330.TW")
    period = st.selectbox("區間", ["1mo","3mo","6mo","1y","2y","5y"], index=3)
    interval = st.selectbox("K線週期", ["1d","1h","30m","15m","5m"], index=0)

    show_ma = st.checkbox("顯示 MA", value=True)
    ma_len = st.number_input("MA 週期", 5, 200, 20)

    show_ema = st.checkbox("顯示 EMA", value=True)
    ema_len = st.number_input("EMA 週期", 5, 200, 60)

    st.markdown("---")
    load_btn = st.button("📥 載入資料")

# === Load Data ===
@st.cache_data(ttl=300)
def load_data(sym, period, interval):
    df = yf.download(sym, period=period, interval=interval)
    df.reset_index(inplace=True)
    return df

if load_btn:
    df = load_data(symbol, period, interval)

    if df.empty:
        st.error("抓不到資料，請確認代碼")
        st.stop()

    # === 指標 ===
    if show_ma:
        df["MA"] = df["Close"].rolling(ma_len).mean()
    if show_ema:
        df["EMA"] = df["Close"].ewm(span=ema_len, adjust=False).mean()

    # === Plot ===
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.75, 0.25],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # --- K棒 ---
    fig.add_trace(go.Candlestick(
        x=df["Datetime"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="K棒",
        increasing=dict(
            line=dict(color="#d62728", width=1),
            fillcolor="rgba(0,0,0,0)"
        ),
        decreasing=dict(
            line=dict(color="#2ca02c", width=1),
            fillcolor="rgba(0,0,0,0)"
        ),
        whiskerwidth=0.5
    ), row=1, col=1)

    # --- MA / EMA ---
    if show_ma:
        fig.add_trace(go.Scatter(
            x=df["Datetime"], y=df["MA"],
            mode="lines", name=f"MA{ma_len}",
            line=dict(width=1.5, color="#1f77b4")
        ), row=1, col=1)

    if show_ema:
        fig.add_trace(go.Scatter(
            x=df["Datetime"], y=df["EMA"],
            mode="lines", name=f"EMA{ema_len}",
            line=dict(width=1.5, color="#ff7f0e")
        ), row=1, col=1)

    # --- Volume ---
    fig.add_trace(go.Bar(
        x=df["Datetime"],
        y=df["Volume"],
        name="成交量",
        marker_line_width=0,
        opacity=0.6
    ), row=2, col=1)

    # === Layout ===
    fig.update_layout(
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_xaxes(showgrid=False, showline=True, linecolor="#cccccc")
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee", showline=True, linecolor="#cccccc")

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("請在左側設定後點「📥 載入資料」")

