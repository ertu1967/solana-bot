import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
from datetime import datetime

# --- SAYFA AYARLARI (MAKYAJ) ---
st.set_page_config(page_title="SOLANA WAR ROOM", layout="wide", page_icon="⚔️")

# --- CSS (STİL - SİYAH VE ALTIN) ---
st.markdown("""
<style>
    .metric-card {background-color: #0e1117; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px; font-weight: bold; color: #ffd700;}
    .status-safe {color: #00ff00; font-weight: bold;}
    .status-danger {color: #ff0000; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE (HAFIZA) ---
# Sayfa yenilense bile verileri unutma
if 'highest_price' not in st.session_state:
    st.session_state.highest_price = 0.0
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- YAN MENÜ (AYARLAR) ---
st.sidebar.title("⚙️ KOMUTA MERKEZİ")
st.sidebar.markdown("---")
symbol = st.sidebar.text_input("Varlık", value="SOL-USD")
drop_percent = st.sidebar.slider("Düşüş Limiti (%)", 1, 30, 18) / 100
refresh_rate = st.sidebar.slider("Yenileme (Saniye)", 5, 300, 60)
run_bot = st.sidebar.checkbox("🚀 SİSTEMİ BAŞLAT", value=False)

# --- ANA EKRAN ---
st.title(f"⚔️ {symbol} - NİHAİ SAVAŞ ODASI")
st.markdown("### *Algoritmik Takip Sistemi*")

# Yer tutucular (Veriler buraya canlı akacak)
col1, col2, col3, col4 = st.columns(4)
chart_placeholder = st.empty()
log_placeholder = st.expander("📝 İŞLEM GÜNLÜĞÜ", expanded=True)

def get_data():
    data = yf.download(symbol, period="1d", interval="5m", progress=False)
    return data

# --- BOT MANTIĞI ---
if run_bot:
    while True:
        # 1. VERİ ÇEK
        df = get_data()
        if not df.empty:
            current_price = df['Close'].iloc[-1]
            current_price = float(current_price) # Sayıya çevir
            
            # 2. ZİRVE GÜNCELLE
            if current_price > st.session_state.highest_price:
                st.session_state.highest_price = current_price
                st.toast(f"YENİ ZİRVE: {current_price}", icon="🚀")
            
            # 3. HESAPLAMALAR
            stop_price = st.session_state.highest_price * (1 - drop_percent)
            mesafe = ((current_price - stop_price) / current_price) * 100
            
            # 4. KUTULARI GÜNCELLE
            with col1:
                st.metric("ANLIK FİYAT", f"${current_price:.2f}", delta_color="normal")
            with col2:
                st.metric("ZİRVE (HWM)", f"${st.session_state.highest_price:.2f}")
            with col3:
                st.metric("STOP SEVİYESİ", f"${stop_price:.2f}", delta=f"-{drop_percent*100}%")
            with col4:
                durum = "GÜVENLİ ✅" if current_price > stop_price else "SAT 🚨"
                st.error(durum) if "SAT" in durum else st.success(durum)

            # 5. GRAFİK ÇİZ (MUM GRAFİĞİ)
            fig = go.Figure(data=[go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'])])
            
            # Stop çizgisini ekle
            fig.add_hline(y=stop_price, line_dash="dash", line_color="red", annotation_text="STOP")
            fig.update_layout(title="Canlı Piyasa Analizi", template="plotly_dark", height=400)
            chart_placeholder.plotly_chart(fig, use_container_width=True)

            # 6. LOG SİSTEMİ
            now = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{now}] Fiyat: {current_price} | Stop: {stop_price:.2f}"
            st.session_state.logs.insert(0, log_entry) # En başa ekle
            
            with log_placeholder:
                st.write(st.session_state.logs[:10]) # Son 10 logu göster

            # SATIŞ TETİĞİ
            if current_price <= stop_price and st.session_state.highest_price > 0:
                st.error(f"!!! TETİK ÇEKİLDİ !!! SATIŞ FİYATI: {current_price}")
                st.balloons() # Görsel uyarı
                st.session_state.highest_price = 0 # Sıfırla
                time.sleep(10)

        # BEKLEME
        time.sleep(refresh_rate)
        st.rerun() # Sayfayı yenile
else:
    st.info("Sistemi başlatmak için soldaki menüden 'SİSTEMİ BAŞLAT' kutusunu işaretle.")