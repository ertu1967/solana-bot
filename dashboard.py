import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime

# --- 1. AYARLAR & STİL ---
st.set_page_config(page_title="WAR ROOM - ELITE", layout="wide", page_icon="🦁")

# CSS: Simsiyah, Zengin ve Net
st.markdown("""
<style>
    .stApp {background-color: #000000;}
    .metric-card {background-color: #111; border: 1px solid #333; padding: 15px; border-radius: 8px;}
    h1, h2, h3 {color: #ffffff; font-family: 'Arial Black', sans-serif;}
    .stSelectbox label {color: #f0f0f0; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 2. ZENGİN PORTFÖY LİSTESİ ---
COINS = {
    "BTC-USD": "BITCOIN (KRAL)",
    "ETH-USD": "ETHEREUM (PRENS)",
    "SOL-USD": "SOLANA (HIZ)",
    "RENDER-USD": "RENDER (GÖZBEBEĞİ)",
    "AVAX-USD": "AVALANCHE (KALE)",
    "FET-USD": "FET AI (ZEKA)",
    "LINK-USD": "CHAINLINK (KÖPRÜ)"
}

# --- 3. TEKNİK ANALİZ MOTORU ---
def calculate_indicators(df):
    # SMA 20 (Trend Yönü)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    
    # RSI 14 (Aşırı Alım/Satım)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 4. YAN MENÜ ---
st.sidebar.markdown("## 🦅 KOMUTA MERKEZİ")
selected_ticker = st.sidebar.selectbox("HEDEF SEÇ", list(COINS.keys()), format_func=lambda x: COINS[x])
refresh_rate = st.sidebar.slider("Yenileme (Sn)", 10, 60, 30)

# --- 5. ANA EKRAN & VERİ ---
st.title(f"⚔️ {COINS[selected_ticker]}")

# Veri Çekme (Son 5 gün, 15dk periyot - Trendi görmek için)
try:
    df = yf.download(selected_ticker, period="5d", interval="15m", progress=False)
    
    if not df.empty:
        df = calculate_indicators(df)
        last_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        
        # Anlık Değerler
        price = float(last_bar['Close'])
        rsi = float(last_bar['RSI'])
        sma = float(last_bar['SMA20'])
        day_high = float(df['High'].tail(96).max()) # Son 24 saat (15dk x 96 bar)
        
        # Sinyal Mantığı (Basit ve Ölümcül)
        trend = "YUKARI 🚀" if price > sma else "AŞAĞI 🔻"
        rsi_durum = "AŞIRI ALIM (Satış Riski)" if rsi > 70 else "AŞIRI SATIM (Fırsat)" if rsi < 30 else "NÖTR"
        
        # --- METRİKLER ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("FİYAT", f"${price:,.2f}", f"%{((price - prev_bar['Close'])/prev_bar['Close']*100):.2f}")
        col2.metric("TREND (SMA20)", trend, f"${sma:,.2f}")
        col3.metric("RSI GÜCÜ", f"{rsi:.1f}", rsi_durum)
        col4.metric("24SAAT ZİRVE", f"${day_high:,.2f}")

        # --- GRAFİK ---
        fig = go.Figure()

        # Mumlar
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'], name='Fiyat'))
        
        # Trend Çizgisi
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='cyan', width=1.5), name='Trend (SMA20)'))

        fig.update_layout(
            template="plotly_dark",
            height=600,
            title=f"{selected_ticker} - TEKNİK GÖRÜNÜM",
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Karar Destek Kutusu
        if rsi < 30 and price > sma:
            st.success("✅ **SİNYAL: GÜÇLÜ ALIM FIRSATI** (Trend yukarı, fiyat ucuzlamış!)")
        elif rsi > 75:
            st.error("⚠️ **SİNYAL: KÂR ALMA BÖLGESİ** (Fiyat çok şişti, düzeltme gelebilir!)")
        else:
            st.info("ℹ️ **SİNYAL: BEKLEME MODU** (Fiyat dengeleniyor, acele etme.)")
            
    else:
        st.error("Piyasa verisi alınamadı. Ticker sembolünü kontrol et.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")

# --- 6. CANLI DÖNGÜ ---
st.caption(f"Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(refresh_rate)
st.rerun()
