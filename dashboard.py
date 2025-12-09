import streamlit as st
import yfinance as yf
import pandas as pd

# --- AYARLAR ---
st.set_page_config(page_title="GERÇEKÇİ DİP ORANLARI", layout="wide", page_icon="🧮")

# Senin Takip Ettiklerin
COINS = ["BTC-USD", "ETH-USD", "SOL-USD", "RENDER-USD", "AVAX-USD"]

def calculate_ideal_dip(ticker):
    # Son 6 Ayın Verisi
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty: return 0, 0
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
    
    # Zirveden Düşüşleri Hesapla (Drawdown)
    rolling_max = df['High'].cummax()
    daily_drawdown = (df['Low'] - rolling_max) / rolling_max
    
    # Gürültüyü At: Sadece %5'ten büyük, %40'tan küçük düşüşleri al (Çöküşleri değil düzeltmeleri arıyoruz)
    significant_dips = daily_drawdown[(daily_drawdown < -0.05) & (daily_drawdown > -0.40)]
    
    if len(significant_dips) > 0:
        # Ortalama Düşüş
        avg_dip = abs(significant_dips.mean()) * 100
        # Maksimum "Normal" Düşüş (En kötü senaryo değil, sık görülen dip)
        common_max_dip = abs(significant_dips.quantile(0.2)) * 100 
    else:
        avg_dip = 10 # Veri yoksa standart
        common_max_dip = 15
        
    return avg_dip, common_max_dip

st.title("🧮 SENİN ORANLAR vs PİYASA GERÇEĞİ")
st.info("Bu tablo, son 6 ayda 'Alım Fırsatı' veren ortalama düşüşleri gösterir.")

results = []
for ticker in COINS:
    avg, max_dip = calculate_ideal_dip(ticker)
    results.append({
        "COIN": ticker.replace("-USD", ""),
        "ORTALAMA DÜŞÜŞ (%)": f"%{avg:.1f}",
        "İDEAL ALIM NOKTASI": f"-%{max_dip:.1f} (Daha Güvenli)",
        "YORUM": "AĞIR VAKUR" if avg < 15 else "ÇOK OYNAK"
    })

df_res = pd.DataFrame(results)
st.table(df_res)
