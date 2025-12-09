import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="WAR ROOM - QUAD SNIPER", layout="wide", page_icon="🦅")

# --- 2. HEDEF LİSTESİ ---
ASSETS = {
    "BTC-USD":  {"name": "BITCOIN",  "type": "AĞIR ABİ 🛡️"},
    "ETH-USD":  {"name": "ETHEREUM", "type": "PRENS 💠"},
    "SOL-USD":  {"name": "SOLANA",   "type": "HIZLI ⚡"},
    "RENDER-USD": {"name": "RENDER", "type": "DELİ FİŞEK 🎨"}
}

# --- 3. MOTOR VE ZEKA ---
def get_usd_try():
    try:
        return yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
    except:
        return 34.50

def analyze_asset_character(ticker, usd_try):
    # 1. Son 6 Ayın Verisini Çek
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)

    # 2. Düşüşleri (Drawdown) Hesapla
    # Her günün zirvesinden olan kaybı buluyoruz
    rolling_max = df['High'].cummax()
    drawdown = (df['Low'] - rolling_max) / rolling_max
    
    # 3. Karakter Analizi (Ortalama Derin Düşüşü Bul)
    # Sadece %5'ten büyük düşüşleri ciddiye al (Gürültüyü filtrele)
    significant_dips = drawdown[drawdown < -0.05]
    
    if len(significant_dips) > 0:
        # En kötü 10 günü değil, ortalama düzeltme karakterini alıyoruz
        avg_drawdown = significant_dips.mean() 
    else:
        # Hiç düşmediyse (İmkansız ama) varsayılan %10
        avg_drawdown = -0.10
        
    # Negatif sayıyı pozitife çevir (Örn: -0.15 -> 0.15)
    drop_pct = abs(avg_drawdown)
    multiplier = 1 - drop_pct # Çarpan (Örn: 0.85)

    # 4. Güncel Durum ve Hedefler
    current_price_usd = df['Close'].iloc[-1]
    local_peak_usd = df['High'].tail(20).max() # Son 20 günün zirvesi (Yakın Takip)
    
    target_entry_usd = local_peak_usd * multiplier
    
    # Zirveden şu anki uzaklık
    distance_from_peak = ((current_price_usd - local_peak_usd) / local_peak_usd) * 100
    
    return {
        "price_tl": current_price_usd * usd_try,
        "peak_tl": local_peak_usd * usd_try,
        "target_tl": target_entry_usd * usd_try,
        "drop_pct": drop_pct * 100,     # Örn: 15.4 (Yüzde)
        "multiplier": multiplier,       # Örn: 0.84
        "distance": distance_from_peak, # Örn: -12.5
        "is_buy": distance_from_peak <= (avg_drawdown * 100) # Hedefe geldi mi?
    }

# --- 4. ARAYÜZ ---
usd_try = get_usd_try()

st.title("🦅 BÜYÜK DÖRTLÜ: DİNAMİK KALİBRASYON")
st.markdown(f"**KUR:** ₺{usd_try:.2f} | **STRATEJİ:** Her varlığın kendi 6 aylık düşüş karakterine göre *özel* dip tahmini.")
st.markdown("---")

# 4 Kolon aç (Her coin için bir tane)
cols = st.columns(4)

for i, (ticker, info) in enumerate(ASSETS.items()):
    with cols[i]:
        # Hesaplamayı yap
        data = analyze_asset_character(ticker, usd_try)
        
        if data:
            # Kart Başlığı
            st.subheader(f"{info['name']}")
            st.caption(f"{info['type']}")
            
            # Dinamik Oran Göstergesi
            st.metric("KARAKTER (Ort. Düşüş)", f"%{data['drop_pct']:.1f}", help="Bu coinin son 6 ayda zirveden ortalama düşüş huyu.")
            
            st.markdown("---")
            
            # Fiyatlar
            st.markdown(f"**ZİRVE (20 Gün):** ₺{data['peak_tl']:,.0f}")
            st.markdown(f"**ŞU AN:** ₺{data['price_tl']:,.0f}")
            
            # Hedef Analizi
            target_color = "green" if data['is_buy'] else "orange"
            st.markdown(f":{target_color}[**HEDEF GİRİŞ:**] **₺{data['target_tl']:,.0f}**")
            
            # Durum Çubuğu
            st.progress(min(1.0, abs(data['distance']) / data['drop_pct']))
            
            # Karar
            if data['is_buy']:
                st.success(f"🔥 **ALIM ZAMANI!**\n\nFiyat beklenen %{data['drop_pct']:.1f} düşüşü yaptı.")
            else:
                kalan = data['price_tl'] - data['target_tl']
                st.info(f"✋ **BEKLE.**\n\nHedefe **₺{kalan:,.0f}** var.")
                st.caption(f"Şu an Zirveden Uzaklık: %{data['distance']:.1f}")
                
        else:
            st.error("Veri Yok")

# --- 5. TABLO ÖZETİ ---
st.markdown("---")
st.subheader("📋 KOMUTA MERKEZİ ÖZETİ")

summary_data = []
for ticker, info in ASSETS.items():
    d = analyze_asset_character(ticker, usd_try)
    if d:
        summary_data.append({
            "VARLIK": info['name'],
            "TİP": info['type'],
            "ÇARPAN (Risk)": f"{d['multiplier']:.2f}x",
            "GEREKEN DÜŞÜŞ": f"%{d['drop_pct']:.1f}",
            "ANLIK DÜŞÜŞ": f"%{d['distance']:.1f}",
            "DURUM": "✅ AL" if d['is_buy'] else "⏳ BEKLE"
        })

df_sum = pd.DataFrame(summary_data)
st.table(df_sum)

if st.button("YENİLE"):
    st.rerun()
