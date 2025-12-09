import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="WAR ROOM - TL MODU", layout="wide", page_icon="🇹🇷")

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

# --- 3. YARDIMCI FONKSİYONLAR ---
def get_dolar_kuru():
    try:
        # Anlık Dolar/TL kurunu çeker
        ticker = yf.Ticker("TRY=X")
        hist = ticker.history(period="1d")
        return float(hist['Close'].iloc[-1])
    except:
        return 34.50 # Acil durum yedeği (Data gelmezse)

def calculate_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1) 

    # SMA 20
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 4. YAN MENÜ ---
st.sidebar.markdown("## 🇹🇷 TL KOMUTA MERKEZİ")
selected_ticker = st.sidebar.selectbox("VARLIK SEÇ", list(COINS.keys()), format_func=lambda x: COINS[x])
refresh_rate = st.sidebar.slider("Yenileme (Sn)", 10, 60, 30)

# Dolar Kurunu Al
dolar_kuru = get_dolar_kuru()
st.sidebar.metric("ANLIK DOLAR KURU", f"₺{dolar_kuru:.2f}")

# --- 5. ANA EKRAN & VERİ ---
st.title(f"⚔️ {COINS[selected_ticker]} (TL BAZLI)")

try:
    # Veriyi Dolar olarak çekiyoruz (Global veri daha sağlıklıdır)
    df = yf.download(selected_ticker, period="5d", interval="15m", progress=False)
    
    if not df.empty:
        df = calculate_indicators(df)
        
        # --- TL DÖNÜŞÜMÜ ---
        # Bütün seriyi dolar kuruyla çarpıyoruz ki grafik TL olsun
        df['Close_TRY'] = df['Close'] * dolar_kuru
        df['Open_TRY'] = df['Open'] * dolar_kuru
        df['High_TRY'] = df['High'] * dolar_kuru
        df['Low_TRY'] = df['Low'] * dolar_kuru
        df['SMA20_TRY'] = df['SMA20'] * dolar_kuru

        last_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        
        # TL Fiyatlar
        price = float(last_bar['Close_TRY'])
        prev_price = float(prev_bar['Close_TRY'])
        
        # Teknik Göstergeler (RSI değişmez, oran aynıdır)
        rsi = float(last_bar['RSI'])
        sma = float(last_bar['SMA20_TRY'])
        day_high = float(df['High_TRY'].tail(96).max()) 
        
        degisim = ((price - prev_price) / prev_price) * 100
        
        trend = "YUKARI 🚀" if price > sma else "AŞAĞI 🔻"
        rsi_durum = "AŞIRI ALIM (Satış Riski)" if rsi > 70 else "AŞIRI SATIM (Fırsat)" if rsi < 30 else "NÖTR"
        
        # --- METRİKLER (TL SİMGESİYLE) ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("FİYAT (TL)", f"₺{price:,.2f}", f"%{degisim:.2f}")
        col2.metric("TREND (SMA20)", trend, f"₺{sma:,.2f}")
        col3.metric("RSI GÜCÜ", f"{rsi:.1f}", rsi_durum)
        col4.metric("24S ZİRVE (TL)", f"₺{day_high:,.2f}")

        # --- GRAFİK (TL) ---
        fig = go.Figure()

        # Mumlar (TL Verisiyle)
        fig.add_trace(go.Candlestick(x=df.index, 
                                     open=df['Open_TRY'], 
                                     high=df['High_TRY'],
                                     low=df['Low_TRY'], 
                                     close=df['Close_TRY'], 
                                     name='Fiyat (TL)'))
        
        # Trend Çizgisi
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20_TRY'], line=dict(color='orange', width=1.5), name='Trend (SMA20)'))

        fig.update_layout(
            height=600,
            title=f"{selected_ticker} - TÜRK LİRASI GRAFİĞİ",
            xaxis_rangeslider_visible=False,
            yaxis_title="Fiyat (TRY)",
            yaxis_tickprefix="₺"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Karar Kutuları
        if rsi < 30 and price > sma:
            st.success("✅ **SİNYAL: GÜÇLÜ ALIM FIRSATI** (TL bazında ucuzladı!)")
        elif rsi > 75:
            st.error("⚠️ **SİNYAL: KÂR ALMA BÖLGESİ** (Çok yükseldi, dikkat!)")
        else:
            st.info("ℹ️ **SİNYAL: BEKLEME MODU** (Piyasa karar aşamasında.)")
            
    else:
        st.error("Veri yok.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")

# --- 6. DÖNGÜ ---
time.sleep(refresh_rate)
st.rerun()
