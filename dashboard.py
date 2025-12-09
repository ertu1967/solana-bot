import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="WAR ROOM - 10 DAY SNIPER", layout="wide", page_icon="⚡")

# --- 2. HEDEF LİSTESİ ---
ASSETS = {
    "BTC-USD":  {"name": "BITCOIN",  "type": "KRAL 🛡️"},
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
    # 1. KARAKTER ANALİZİ (Son 6 Ayın Düşüş Huyunu Öğren)
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)

    # Düşüşleri Hesapla
    rolling_max = df['High'].cummax()
    drawdown = (df['Low'] - rolling_max) / rolling_max
    
    # Ortalama Anlamlı Düşüşü Bul (%5 üzeri düşüşler)
    significant_dips = drawdown[drawdown < -0.05]
    
    if len(significant_dips) > 0:
        avg_drawdown = significant_dips.mean() 
    else:
        avg_drawdown = -0.10 # Varsayılan
        
    drop_pct = abs(avg_drawdown)    # Örn: 0.15
    multiplier = 1 - drop_pct       # Örn: 0.85

    # 2. HEDEF ANALİZİ (GÜNCELLEME BURADA: SON 10 GÜN)
    current_price_usd = df['Close'].iloc[-1]
    
    # --- KRİTİK DEĞİŞİKLİK: .tail(10) ---
    local_peak_usd = df['High'].tail(10).max() 
    
    target_entry_usd = local_peak_usd * multiplier
    
    # Zirveden şu anki uzaklık
    distance_from_peak = ((current_price_usd - local_peak_usd) / local_peak_usd) * 100
    
    return {
        "price_tl": current_price_usd * usd_try,
        "peak_tl": local_peak_usd * usd_try,
        "target_tl": target_entry_usd * usd_try,
        "drop_pct": drop_pct * 100,     
        "multiplier": multiplier,       
        "distance": distance_from_peak, 
        "is_buy": distance_from_peak <= (avg_drawdown * 100)
    }

# --- 4. ARAYÜZ ---
usd_try = get_usd_try()

st.title("⚡ 10 GÜNLÜK HIZLI AVCI MODU")
st.markdown(f"**KUR:** ₺{usd_try:.2f} | **STRATEJİ:** Sadece son **10 GÜNÜN** zirvesini baz alıyoruz. Eski hikayeler çöp.")
st.markdown("---")

cols = st.columns(4)

for i, (ticker, info) in enumerate(ASSETS.items()):
    with cols[i]:
        data = analyze_asset_character(ticker, usd_try)
        
        if data:
            st.subheader(f"{info['name']}")
            st.caption(f"{info['type']}")
            
            # Dinamik Oran
            st.metric("KARAKTER (Beklenen Düşüş)", f"%{data['drop_pct']:.1f}", help="Bu coinin huyu bu kadar düşmek.")
            
            st.markdown("---")
            
            # Fiyatlar
            st.markdown(f"**10 GÜNLÜK ZİRVE:** ₺{data['peak_tl']:,.0f}")
            st.markdown(f"**ŞU AN:** ₺{data['price_tl']:,.0f}")
            
            # Hedef Analizi
            target_color = "green" if data['is_buy'] else "red"
            st.markdown(f":{target_color}[**HEDEF GİRİŞ:**] **₺{data['target_tl']:,.0f}**")
            
            # Çubuk
            progress_val = min(1.0, abs(data['distance']) / data['drop_pct'])
            st.progress(progress_val)
            
            # Karar
            if data['is_buy']:
                st.success(f"🚀 **SALDIR!**\n\nFiyat 10 günlük zirveden beklenen %{data['drop_pct']:.1f} düşüşü yaptı.")
            else:
                kalan = data['price_tl'] - data['target_tl']
                st.error(f"✋ **BEKLE.**\n\nFırsata **₺{kalan:,.0f}** var.")
                st.caption(f"Şu anki düşüş: %{data['distance']:.1f}")
                
        else:
            st.error("Veri Yok")

st.markdown("---")
if st.button("PİYASAYI TARA (YENİLE)"):
    st.rerun()
