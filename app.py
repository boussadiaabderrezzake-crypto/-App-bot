import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="SMART TRADING AI", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .main-title { color: #d4af37; text-align: center; font-size: 2.2rem; font-weight: bold; }
    .sub-title { color: #58a6ff; text-align: center; font-size: 1.1rem; margin-bottom: 2rem; }
    .stButton>button { background-color: #1f6feb; color: white; border-radius: 6px; width: 100%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

TELEGRAM_TOKEN = "9206676062:AAH8_U0dY7UDCbJFQiNvoJ0p3EjmOf-ZzwI"
TELEGRAM_CHAT_ID = "-1003911614530"

def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

def calculate_obv(df):
    return (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

def fetch_data(symbol, period="5d", interval="5m"):
    if symbol == "XAUUSD":
        ticker_symbol = "GC=F"
    elif symbol == "XAGUSD":
        ticker_symbol = "SI=F"
    elif symbol == "EURUSD":
        ticker_symbol = "EURUSD=X"
    elif symbol == "BTCUSD":
        ticker_symbol = "BTC-USD"
    else:
        ticker_symbol = symbol
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)
    return df

def analyze_smc(df):
    if len(df) < 50:
        return None
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    df['OBV'] = calculate_obv(df)
    df['OBV_MA'] = df['OBV'].rolling(window=20).mean()
    
    last_close = df['Close'].iloc[-1]
    sma50 = df['SMA50'].iloc[-1]
    sma200 = df['SMA200'].iloc[-1]
    obv = df['OBV'].iloc[-1]
    obv_ma = df['OBV_MA'].iloc[-1]
    
    fvg_type = None
    if len(df) >= 3:
        if df['Low'].iloc[-1] > df['High'].iloc[-3]:
            fvg_type = "Bullish FVG"
        elif df['High'].iloc[-1] < df['Low'].iloc[-3]:
            fvg_type = "Bearish FVG"

    structure = "عرضي"
    signal = "NEUTRAL"
    if last_close > sma50 and sma50 > sma200 and obv > obv_ma:
        structure = "BOS صاعد"
        signal = "BUY"
    elif last_close < sma50 and sma50 < sma200 and obv < obv_ma:
        structure = "BOS هابط"
        signal = "SELL"
        
    return {
        "price": last_close,
        "structure": structure,
        "signal": signal,
        "fvg": fvg_type or "لا يوجد",
        "obv_status": "سيولة صاعدة" if obv > obv_ma else "سيولة هابطة",
    }

st.markdown('<div class="main-title">🌟 SMART TRADING AI 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">GOLDRIDER & RAZAKE TRADING</div>', unsafe_allow_html=True)

st.sidebar.header("لوحة التحكم")
symbol = st.sidebar.selectbox("اختر الزوج:", ["XAUUSD", "XAGUSD", "EURUSD", "BTCUSD", "AAPL", "TSLA"])
timeframe = st.sidebar.selectbox("الإطار الزمني:", ["5m", "15m", "1h", "1d"])

period = "5d" if timeframe in ["5m", "15m"] else "1mo"
data = fetch_data(symbol, period=period, interval=timeframe)

tab1, tab2, tab3 = st.tabs(["التحليل المباشر", "حاسبة المخاطر", "معلومات"])

with tab1:
    if not data.empty:
        results = analyze_smc(data)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("السعر", f"${results['price']:.2f}")
        col2.metric("الإشارة", results['signal'])
        col3.metric("OBV", results['obv_status'])
        col4.metric("FVG", results['fvg'])
        
        st.markdown("---")
        col_chart, col_info = st.columns([2, 1])
        
        with col_chart:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_info:
            st.write(f"**هيكل السوق:** {results['structure']}")
            entry = results['price']
            
            if results['signal'] == "BUY":
                sl = entry - 5.0
                tp1 = entry + 5.0
                tp2 = entry + 10.0
                tp3 = entry + 15.0
                tp4 = entry + 20.0
            else:
                sl = entry + 5.0
                tp1 = entry - 5.0
                tp2 = entry - 10.0
                tp3 = entry - 15.0
                tp4 = entry - 20.0
                
            st.write(f"🛑 **وقف الخسارة:** `{sl:.2f}` (5$)")
            st.write(f"🎯 **الهدف 1:** `{tp1:.2f}` (5$)")
            st.write(f"🎯 **الهدف 2:** `{tp2:.2f}` (10$)")
            st.write(f"🎯 **الهدف 3:** `{tp3:.2f}` (15$)")
            st.write(f"🎯 **الهدف 4:** `{tp4:.2f}` (20$)")
            
            if st.button("📲 إرسال التقرير لتليجرام"):
                msg = f"🌟 *GOLDRIDER AI* 🌟\n\n"
                msg += f"📈 *الزوج:* {symbol}\n"
                msg += f"🔹 *الإشارة:* `{results['signal']}`\n"
                msg += f"💰 *الدخول:* `{entry:.2f}`\n"
                msg += f"🛑 *الستوب:* `{sl:.2f}` (5$)\n"
                msg += f"🎯 *الأهداف:* `{tp1:.2f}` | `{tp2:.2f}` | `{tp3:.2f}` | `{tp4:.2f}`\n\n"
                msg += f"📌 *ملاحظة:* يتم تأمين الصفقة عند +5$."
                send_telegram_alert(msg)
                st.success("تم الإرسال إلى تيليجرام بنجاح!")

with tab2:
    st.subheader("حاسبة إدارة المخاطر")
    balance = st.number_input("رأس المال ($)", value=1000.0)
    risk = st.number_input("نسبة المخاطرة (%)", value=1.0)
    entry_price = st.number_input("سعر الدخول", value=2000.0)
    sl_price = st.number_input("سعر وقف الخسارة", value=1995.0)
    
    if entry_price != sl_price:
        risk_amount = balance * (risk / 100)
        lot_size = risk_amount / abs(entry_price - sl_price)
        st.metric("حجم العقد المناسب", f"{lot_size:.2f}")

with tab3:
    st.info("تطبيق SMART TRADING AI - GOLDRIDER & RAZAKE TRADING")
    st.write("**الأهداف:** 4 أهداف (5$، 10$، 15$، 20$).")
    st.write("**وقف الخسارة:** 5$.")
    st.write("**التأمين:** عند +5$ (نقل الوقف للدخول).")
    st.write("**الأصول المدعومة:** الذهب، الفضة، الفوركس، العملات الرقمية، الأسهم.")
