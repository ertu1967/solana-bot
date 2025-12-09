import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
from datetime import datetime

# --- 1. SAVAŞ ALANI AYARLARI ---
st.set_page_config(page_title="SOLANA WAR ROOM", layout="wide", page_icon="⚔️")

# CSS: Siyah ve Altın. Zengin işi.
st.markdown("""
<style>
    .metric-card {background-color: #0e1117; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center;}
    .big-font {font-size: 24px; font-weight: bold; color: #ffd700;}
</style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA (BEYİN) ---
# Burası kritik. Sayfa yenilense de sistemin açık olduğunu unutmayacak.
if 'highest_price' not in st.session_state:
    st.session_state.highest_price = 0.0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'sistem_acik' not in st.session_state:
    st.session_state.sistem_acik = False  # Başlangıçta kapalı

# --- 3. KOMUTA MERKEZİ (SOL MENÜ) ---
st.sidebar.title("⚙️ KOMUTA MERKEZİ")
st.sidebar.markdown("---")
symbol = st.sidebar.text_input("Varlık", value="SOL-USD")
drop_percent = st.sidebar.slider("Düşüş Limiti (%)", 1, 30, 18) / 100
refresh_rate = st.sidebar.slider("Yenileme (Saniye)", 5, 300, 60)

# Checkbox'ı doğrudan hafızaya (key='sistem_acik') bağlıyoruz.
# Artık sayfayı yenilesen de tikli kalır.
st.sidebar.checkbox("🚀 SİSTEMİ BAŞLAT", key="sistem_acik")

# --- 4. ANA EKRAN ---
st.title(f"⚔️ {symbol} - NİHAİ SAVAŞ ODASI")
st.markdown("### *Algoritmik Takip Sistemi*")

col1, col2, col3, col4 = st.columns(4)
chart_placeholder = st.empty()
log_placeholder = st.expander("📝 İŞLEM GÜNLÜĞÜ", expanded=True)

def get_data():
    # Progress bar kapatıldı, temiz veri.
    data = yf.download(symbol, period="1d", interval="5m", progress=False)
    return data

# --- 5. BOT MANTIĞI ---
# While True DÖNGÜSÜ YOK! Streamlit zaten loop mantığıyla çalışır.
# Sonsuz döngü tarayıcıyı kilitler. Onun yerine kontrollü rerun kullanıyoruz.

if st.session_state.sistem_acik:
    # Veriyi Çek
    df = get_data()
    
    if not df.empty:
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
        
        # --- KRİTİK DÜZELTME (O saçma yazıları burası engelliyor) ---
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
        fig.update_layout(title="Canlı Piyasa Analizi", template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0))
        chart_placeholder.plotly_chart(fig, use_container_width=True)

        # --- LOGLAMA ---
        now = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{now}] Fiyat: {current_price} | Stop: {stop_price:.2f}"
        
        # Log tekrarını önlemek için son log ile aynıysa yazma (Opsiyonel temizlik)
        if not st.session_state.logs or log_entry != st.session_state.logs[0]:
            st.session_state.logs.insert(0, log_entry)
        
        # Logları string olarak yazdır, liste objesi olarak değil
        log_text = "\n".join(st.session_state.logs[:10])
        log_placeholder.text(log_text)

        # --- SATIŞ AKSİYONU ---
        if current_price <= stop_price and st.session_state.highest_price > 0:
            st.error(f"!!! TETİK ÇEKİLDİ !!! SATIŞ FİYATI: {current_price}")
            st.balloons()
            # Burada normalde API ile satış emri gider
            st.session_state.highest_price = 0 # Sıfırla ki döngüye girmesin
            time.sleep(5)

    # --- OTOMATİK YENİLEME ---
    # Python'u uyutuyoruz, sonra sayfayı yeniliyoruz.
    time.sleep(refresh_rate)
    st.rerun()

else:
    # Sistem kapalıyken son durumu göster ama yenileme yapma
    st.info("Sistem Beklemede. Başlatmak için soldaki anahtarı çevir.")
