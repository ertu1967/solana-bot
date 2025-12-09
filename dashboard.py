import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
from datetime import datetime

# --- 1. SAVAŞ ALANI AYARLARI ---
st.set_page_config(page_title="CRYPTO WAR ROOM", layout="wide", page_icon="⚔️")

# CSS: Zengin, Karanlık, Altın.
st.markdown("""
<style>
    .metric-card {background-color: #0e1117; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px; font-weight: bold; color: #ffd700;}
</style>
""", unsafe_allow_html=True)

# --- 2. ZENGİNİN MATEMATİĞİ (CONFIG) ---
# Her coin için özel hesaplanmış risk oranları
COIN_CONFIG = {
    "SOL-USD": 18,  # Amiral
    "ETH-USD": 12,  # Kale (Düşük Risk)
    "SUI-USD": 25,  # Vahşi At (Yüksek Risk)
    "AVAX-USD": 20, # Yedek Güç
    "APT-USD": 28,  # Kumar (Çok Yüksek Risk)
    "NEAR-USD": 22  # Yapay Zeka (Orta-Yüksek)
}

# --- 3. HAFIZA (SESSION STATE) ---
if 'highest_price' not in st.session_state:
    st.session_state.highest_price = 0.0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'sistem_acik' not in st.session_state:
    st.session_state.sistem_acik = False
if 'last_symbol' not in st.session_state:
    st.session_state.last_symbol = "SOL-USD"
# Slider değeri için hafıza
if 'slider_val' not in st.session_state:
    st.session_state.slider_val = COIN_CONFIG["SOL-USD"]

# --- 4. KOMUTA MERKEZİ ---
st.sidebar.title("⚙️ PORTFÖY YÖNETİMİ")
st.sidebar.markdown("---")

# Coin Listesi
watch_list = list(COIN_CONFIG.keys())
symbol = st.sidebar.selectbox("HEDEF SEÇ", watch_list, index=0)

# --- AKILLI GEÇİŞ SİSTEMİ ---
# Coin değişirse; 1. Zirveyi sıfırla, 2. O coin'in risk oranını getir.
if symbol != st.session_state.last_symbol:
    st.session_state.highest_price = 0.0
    st.session_state.logs = []
    st.session_state.last_symbol = symbol
    # Slider'ı o coine özel ayara çek
    st.session_state.slider_val = COIN_CONFIG[symbol]
    st.rerun()

# Slider artık hafızadan besleniyor (key='slider_val')
drop_percent_int = st.sidebar.slider(
    "Düşüş Limiti (%)", 
    min_value=1, 
    max_value=40, 
    value=st.session_state.slider_val,
    key="dynamic_slider" # Bu key ile değeri okuyoruz, ama session_state.slider_val ile set ediyoruz
)

# Slider elle değiştirilirse hafızayı güncelle (ki rerun'da bozulmasın)
st.session_state.slider_val = drop_percent_int
drop_percent = drop_percent_int / 100

refresh_rate = st.sidebar.slider("Yenileme (Saniye)", 5, 300, 60)
st.sidebar.checkbox("🚀 SİSTEMİ BAŞLAT", key="sistem_acik")

# --- 5. ANA EKRAN ---
st.title(f"⚔️ {symbol} - SAVAŞ ODASI")
st.markdown(f"### *Algoritmik Takip: {drop_percent_int}% Stop Marjı*")

col1, col2, col3, col4 = st.columns(4)
chart_placeholder = st.empty()
log_placeholder = st.expander("📝 İŞLEM GÜNLÜĞÜ", expanded=True)

def get_data():
    try:
        data = yf.download(symbol, period="1d", interval="5m", progress=False)
        return data
    except Exception as e:
        st.error(f"Veri hatası: {e}")
        return None

# --- 6. BOT MANTIĞI ---
if st.session_state.sistem_acik:
    df = get_data()
    
    if df is not None and not df.empty:
        current_price = float(df['Close'].iloc[-1])
        
        # Zirve Güncelle
        if current_price > st.session_state.highest_price:
            st.session_state.highest_price = current_price
            st.toast(f"YENİ ZİRVE: ${current_price}", icon="🚀")
        
        # Stop Hesapla
        stop_price = st.session_state.highest_price * (1 - drop_percent)
        
        # --- KUTULARI DOLDUR ---
        col1.metric("ANLIK FİYAT", f"${current_price:.2f}")
        col2.metric("ZİRVE (HWM)", f"${st.session_state.highest_price:.2f}")
        col3.metric("STOP SEVİYESİ", f"${stop_price:.2f}", delta=f"-{drop_percent*100:.0f}%", delta_color="inverse")
        
        with col4:
            durum_metni = "GÜVENLİ ✅" if current_price > stop_price else "SAT 🚨"
            if "SAT" in durum_metni:
                st.error(durum_metni)
            else:
                st.success(durum_metni)

        # --- GRAFİK ---
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'])])
        fig.add_hline(y=stop_price, line_dash="dash", line_color="red", annotation_text="STOP")
        fig.update_layout(title=f"{symbol} Canlı Analiz", template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0))
        chart_placeholder.plotly_chart(fig, use_container_width=True)

        # --- LOGLAMA ---
        now = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{now}] {symbol} Fiyat: {current_price:.2f} | Stop: {stop_price:.2f}"
        
        if not st.session_state.logs or log_entry != st.session_state.logs[0]:
            st.session_state.logs.insert(0, log_entry)
        
        log_text = "\n".join(st.session_state.logs[:10])
        log_placeholder.text(log_text)

        # --- SATIŞ AKSİYONU ---
        if current_price <= stop_price and st.session_state.highest_price > 0:
            st.error(f"!!! TETİK ÇEKİLDİ !!! SATIŞ: {current_price}")
            st.balloons()
            st.session_state.highest_price = 0 
            time.sleep(5)

    # --- OTOMATİK YENİLEME ---
    time.sleep(refresh_rate)
    st.rerun()

else:
    st.info("Sistem Beklemede. Coin'i seç ve soldan başlat.")
