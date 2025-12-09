import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="SNIPER PROTOCOL - WAR ROOM", layout="wide", page_icon="🎯")

# --- 2. HEDEFLER (SENİN SEPET) ---
COINS = {
    "BTC-USD": "BITCOIN",
    "ETH-USD": "ETHEREUM",
    "SOL-USD": "SOLANA",
    "RENDER-USD": "RENDER",
    "AVAX-USD": "AVALANCHE",
    "FET-USD": "FET AI",
    "LINK-USD": "CHAINLINK"
}

# --- 3. FONKSİYONLAR ---
def get_market_data():
    # Dolar Kuru
    try:
        usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
    except:
        usd_try = 34.50 # Yedek
        
    # DXY (Dolar Endeksi) - Filtre için
    try:
        dxy = yf.Ticker("DX-Y.NYB").history(period="1d")['Close'].iloc[-1]
    except:
        dxy = 0

    return usd_try, dxy

def analyze_coin(ticker, usd_try):
    # Son 30 günün verisi (Yerel Zirveyi bulmak için ideal)
    df = yf.download(ticker, period="1mo", interval="1h", progress=False)
    
    if df.empty:
        return None

    # MultiIndex temizliği
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # Verileri Hazırla
    current_price_usd = float(df['Close'].iloc[-1])
    local_peak_usd = float(df['High'].max()) # Son 1 ayın en yükseği
    
    # --- SNIPER MATEMATİĞİ ---
    # Giriş Hedefi: Zirve x 0.82
    target_entry_usd = local_peak_usd * 0.82
    
    # Zirveden Uzaklık (%)
    distance_from_peak = ((current_price_usd - local_peak_usd) / local_peak_usd) * 100
    
    # TL Çevirimi
    data = {
        "current_tl": current_price_usd * usd_try,
        "peak_tl": local_peak_usd * usd_try,
        "entry_target_tl": target_entry_usd * usd_try,
        "distance_pct": distance_from_peak,
        "df": df,
        "status": "ALIM BÖLGESİ 🎯" if distance_from_peak <= -18 else "BEKLE ✋"
    }
    return data

# --- 4. ARAYÜZ BAŞLIYOR ---
usd_try, dxy = get_market_data()

# Kenar Çubuğu (Filtreler)
st.sidebar.markdown("## 🛡️ GÜVENLİK KİLİTLERİ")
st.sidebar.metric("DOLAR KURU (USD/TRY)", f"₺{usd_try:.2f}")
st.sidebar.metric("DXY ENDEKSİ", f"{dxy:.2f}", delta_color="inverse", help="105 üzerindeyse İŞLEM YAPMA!")

if dxy > 105:
    st.sidebar.error("🚨 DXY ÇOK YÜKSEK! NAKİTTE KAL.")
else:
    st.sidebar.success("✅ DXY GÜVENLİ BÖLGEDE.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ KONTROL PANELİ")
selected_ticker = st.sidebar.selectbox("DETAYLI ANALİZ SEÇ", list(COINS.keys()), format_func=lambda x: COINS[x])
refresh = st.sidebar.button("VERİLERİ GÜNCELLE")

# --- 5. RADAR EKRANI (TÜM LİSTE ÖZETİ) ---
st.title("🎯 SNIPER PROTOKOLÜ: RADAR EKRANI")
st.info("💡 **KURAL:** Zirveden **%18** düştüyse tetiği çek. Yoksa izle.")

# Tüm coinleri hızlıca tara ve tablo yap
radar_data = []
cols = st.columns(len(COINS)) # Yan yana metrikler için

for i, (ticker, name) in enumerate(COINS.items()):
    with st.spinner(f"{name} taranıyor..."):
        analiz = analyze_coin(ticker, usd_try)
        if analiz:
            # Tablo verisi
            radar_data.append({
                "COIN": name,
                "FİYAT (TL)": f"₺{analiz['current_tl']:,.2f}",
                "ZİRVE (TL)": f"₺{analiz['peak_tl']:,.2f}",
                "ZİRVEDEN UZAKLIK": f"%{analiz['distance_pct']:.2f}",
                "DURUM": analiz['status']
            })
            
            # Üstteki küçük kartlar (Görsel özet)
            color = "normal"
            if analiz['distance_pct'] <= -18: color = "inverse" # Hedefe geldiyse parlasın
            cols[i].metric(label=name, value=f"%{analiz['distance_pct']:.1f}", delta=analiz['status'], delta_color=color)

# Tabloyu Göster
df_radar = pd.DataFrame(radar_data)
st.table(df_radar.style.apply(lambda x: ['background-color: #1f77b4' if 'ALIM' in v else '' for v in x], subset=['DURUM']))

st.markdown("---")

# --- 6. DETAYLI SAVAŞ PLANI (SEÇİLEN COIN) ---
st.header(f"⚔️ {COINS[selected_ticker]} - OPERASYON PLANI")

# Seçilen coinin detaylı verisini tekrar al (yukarıda döngüde aldık ama detay için df lazım)
detay = analyze_coin(selected_ticker, usd_try)

if detay:
    col1, col2, col3 = st.columns(3)
    
    # 1. ZİHNİYET: Zirve Analizi
    with col1:
        st.subheader("1. ZİRVE ANALİZİ")
        st.metric("SON ZİRVE (30 Gün)", f"₺{detay['peak_tl']:,.2f}")
        st.metric("ŞU ANKİ FİYAT", f"₺{detay['current_tl']:,.2f}")
        st.metric("MESAFE (Hedef % -18)", f"%{detay['distance_pct']:.2f}", help="Bu oran -18 olana kadar bekle.")

    # 2. MATEMATİK: Giriş/Çıkış
    with col2:
        st.subheader("2. EMRİ GİR")
        st.markdown(f"**İDEAL GİRİŞ FİYATI:**")
        st.markdown(f"# 🎯 ₺{detay['entry_target_tl']:,.2f}")
        st.caption(f"(Zirve Fiyatı x 0.82)")
        
        if detay['current_tl'] <= detay['entry_target_tl']:
            st.success("SİNYAL: 🔥 ALIM FIRSATI! FİYAT HEDEFİN ALTINDA.")
        else:
            fark = detay['current_tl'] - detay['entry_target_tl']
            st.warning(f"SABIRLI OL. HEDEFE **₺{fark:,.2f}** DAHA VAR.")

    # 3. ÇIKIŞ PLANI (Eğer Şimdi Alırsan)
    with col3:
        st.subheader("3. GELECEK SENARYOSU")
        if detay['current_tl'] <= detay['entry_target_tl']:
            # Alım yaptıysak hedefler
            satis_hedefi = detay['current_tl'] * 1.35
            stop_loss = detay['current_tl'] * 0.94
            st.metric("SATIŞ HEDEFİ (%35 Kar)", f"₺{satis_hedefi:,.2f}")
            st.metric("STOP LOSS (%6 Zarar)", f"₺{stop_loss:,.2f}", delta_color="inverse")
        else:
            st.info("Henüz alım bölgesinde değiliz. Senaryo hesaplanmadı.")

    # --- GRAFİK ---
    st.subheader("📊 GRAFİK ÜZERİNDE SAVAŞ ALANI")
    
    df_chart = detay['df']
    # TL'ye çevir grafik için
    df_chart['Close_TL'] = df_chart['Close'] * usd_try
    
    fig = go.Figure()
    
    # Fiyat Çizgisi
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close_TL'], mode='lines', name='Fiyat (TL)', line=dict(color='white')))
    
    # Zirve Çizgisi (Kırmızı)
    fig.add_hline(y=detay['peak_tl'], line_dash="dash", line_color="red", annotation_text="ZİRVE (TEPE)")
    
    # İdeal Alım Bölgesi (Yeşil)
    fig.add_hline(y=detay['entry_target_tl'], line_dash="solid", line_color="#00ff00", annotation_text="GİRİŞ HEDEFİ (Zirve x 0.82)", annotation_position="bottom right")

    # Mevcut Fiyatın Durumu
    fig.add_annotation(x=df_chart.index[-1], y=detay['current_tl'],
                       text=f"ŞU AN: %{detay['distance_pct']:.1f}",
                       showarrow=True, arrowhead=1)

    fig.update_layout(template="plotly_dark", height=500, title=f"{COINS[selected_ticker]} - 30 GÜNLÜK TAKİP")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Veri çekilemedi.")

# --- AUTO REFRESH ---
if st.sidebar.checkbox("OTOMATİK YENİLE (30sn)", value=True):
    time.sleep(30)
    st.rerun()
