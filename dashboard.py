import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="WAR ROOM - 24/7", layout="wide", page_icon="🦅")

# CSS: Patron Teması
st.markdown("""
<style>
    .metric-card {background-color: #0e1117; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px; font-weight: bold; color: #ffd700;}
</style>
""", unsafe_allow_html=True)

# --- 2. COIN AYARLARI ---
COIN_CONFIG = {
    "SOL-USD": {"risk": 0.18, "name": "SOLANA"},
    "ETH-USD": {"risk": 0.12, "name": "ETHEREUM"},
    "SUI-USD": {"risk": 0.25, "name": "SUI"},
    "AVAX-USD": {"risk": 0.20, "name": "AVALANCHE"},
    "APT-USD": {"risk": 0.28, "name": "APTOS"},
    "NEAR-USD": {"risk": 0.22, "name": "NEAR PROTOCOL"}
}

# --- 3. YAN MENÜ ---
st.sidebar.title("🦅 GÖZCÜ KULESİ")
symbol = st.sidebar.selectbox("VARLIK SEÇ", list(COIN_CONFIG.keys()))
refresh_rate = st.sidebar.slider("Yenileme Hızı (Sn)", 10, 300, 30)

# Risk Ayarı (Otomatik gelir ama elle değişebilirsin)
default_risk = int(COIN_CONFIG[symbol]["risk"] * 100)
risk_input = st.sidebar.slider("Risk Limiti (%)", 1, 40, default_risk) / 100

st.title(f"⚔️ {COIN_CONFIG[symbol]['name']} - ANALİZ")

# --- 4. AKILLI VERİ ANALİZİ ---
def get_analysis():
    # Son 24 saatin verisini çek (interval 5m)
    # Bu sayede sen uyurken olan zirveyi de görür.
    df = yf.download(symbol, period="1d", interval="5m", progress=False)
    
    if not df.empty:
        # Son kapanış fiyatı
        current_price = float(df['Close'].iloc[-1])
        
        # GÜNÜN ZİRVESİ (High Water Mark)
        # Bot kapalı olsa bile veriden "Günün En Yükseği"ni bulur.
        day_high = float(df['High'].max())
        
        return df, current_price, day_high
    return None, 0, 0

# --- 5. EKRAN ---
df, current_price, day_high = get_analysis()

if df is not None:
    # Stop seviyesini günün zirvesine göre hesapla
    stop_price = day_high * (1 - risk_input)
    
    # Metrikler
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ANLIK FİYAT", f"${current_price:.2f}")
    c2.metric("24SAAT ZİRVE", f"${day_high:.2f}", help="Sen yokken görülen en yüksek seviye")
    c3.metric("STOP SEVİYESİ", f"${stop_price:.2f}", delta=f"-{risk_input*100:.0f}%", delta_color="inverse")
    
    with c4:
        if current_price <= stop_price:
            st.error("🚨 STOP PATLADI! SATIŞ BÖLGESİ")
        else:
            pct_to_stop = ((current_price - stop_price) / current_price) * 100
            st.success(f"GÜVENLİ ✅ (Stop'a %{pct_to_stop:.1f} var)")

    # Grafik
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'])])
    
    # Stop Çizgisi
    fig.add_hline(y=stop_price, line_dash="dash", line_color="red", annotation_text="STOP")
    fig.update_layout(title=f"{symbol} Son 24 Saat Performansı", template="plotly_dark", height=500, margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Son Güncelleme Zamanı
    st.caption(f"Son Kontrol: {datetime.now().strftime('%H:%M:%S')} (Otomatik Yenilenir)")

else:
    st.error("Veri çekilemedi. Piyasa bağlantısını kontrol et.")

# --- 6. DÖNGÜ ---
# Sayfayı canlı tutar
time.sleep(refresh_rate)
st.rerun()
