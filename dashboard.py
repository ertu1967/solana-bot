import streamlit as st
import yfinance as yf
import pandas as pd

# --- AYARLAR (SENİN AGRESİF TARZIN) ---
st.set_page_config(page_title="SENİN SİSTEMİN (AGRESİF)", layout="wide", page_icon="🚀")

# Sadece RENDER ve BTC kıyaslaması yapalım
COINS = ["RENDER-USD", "BTC-USD", "SOL-USD"]
BASLANGIC_KASA = 1000

# SENİN STRATEJİNİN PARAMETRELERİ
DUSUS_LIMITI = 0.12  # Zirveden %12 düştüğünde AL (Senin "kriz" dediğin yer)
KAR_HEDEFI = 0.08    # Dipten %8 tepki verince SAT (Vur-Kaç)
STOP_LOSS = 0.10     # %10 daha düşerse sat (Zorunlu sigorta)

def run_aggressive_backtest(ticker):
    # Son 4 Ay (120 Gün) - Saatlik Veri (Hızlı hareketleri yakalamak için)
    df = yf.download(ticker, period="4mo", interval="1h", progress=False)
    if df.empty: return 0, 0
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
    
    kasa = BASLANGIC_KASA
    pozisyonda = False
    alis_fiyati = 0
    peak_price = df['High'].iloc[0]
    islem_sayisi = 0
    basarili = 0
    
    # Simülasyon
    for i in range(1, len(df)):
        bar = df.iloc[i]
        current_high = float(bar['High'])
        current_low = float(bar['Low'])
        current_close = float(bar['Close'])
        
        # 1. ZİRVE TAKİBİ (Düşüşü hesaplamak için)
        if current_high > peak_price:
            peak_price = current_high
            
        # 2. ALIM KOŞULU (Zirveden %12 düştü mü?)
        target_buy = peak_price * (1 - DUSUS_LIMITI)
        
        if not pozisyonda:
            if current_low <= target_buy:
                alis_fiyati = target_buy # Emrin gerçekleştiğini varsayıyoruz
                pozisyonda = True
                islem_sayisi += 1
                # Alım yaptık, şimdi zirveyi resetlemiyoruz, satışa odaklanıyoruz
        
        # 3. SATIŞ KOŞULU (Vur-Kaç)
        elif pozisyonda:
            # Hedef: Alış fiyatının %8 üstü
            satis_hedefi = alis_fiyati * (1 + KAR_HEDEFI)
            stop_fiyati = alis_fiyati * (1 - STOP_LOSS)
            
            # Kâr Al (TP)
            if current_high >= satis_hedefi:
                kasa = kasa * (1 + KAR_HEDEFI) # Bileşik Getiri (Parayı katlıyoruz)
                pozisyonda = False
                basarili += 1
                peak_price = current_close # Sattıktan sonra zirve takibini sıfırla
            
            # Stop Ol (SL)
            elif current_low <= stop_fiyati:
                kasa = kasa * (1 - STOP_LOSS)
                pozisyonda = False
                peak_price = current_close

    return kasa, islem_sayisi, basarili

# --- SONUÇ EKRANI ---
st.title("🚀 SENİN 'VUR-KAÇ' SİSTEMİN")
st.markdown(f"### Parametreler: %{DUSUS_LIMITI*100:.0f} Düşüşte Al | %{KAR_HEDEFI*100:.0f} Kârda Sat")
st.info("Bu simülasyon kazandığın parayı tekrar işleme sokar (Bileşik Getiri).")

results = []
for ticker in COINS:
    son_kasa, adet, win = run_aggressive_backtest(ticker)
    
    net_kar = son_kasa - BASLANGIC_KASA
    basari_orani = (win / adet * 100) if adet > 0 else 0
    
    results.append({
        "VARLIK": ticker.replace("-USD", ""),
        "SON KASA": f"₺{son_kasa:,.0f}",
        "NET KÂR": f"₺{net_kar:,.0f}",
        "BÜYÜME": f"%{(net_kar/BASLANGIC_KASA)*100:.0f}",
        "İŞLEM SAYISI": adet,
        "BAŞARI ORANI": f"%{basari_orani:.0f}"
    })

df_res = pd.DataFrame(results)
st.table(df_res)

# Yorum
best_asset = df_res.loc[df_res['SON KASA'].str.replace('₺','').str.replace(',','').astype(float).idxmax()]
st.success(f"SENİN MODELİN SONUCU: Eğer **{best_asset['VARLIK']}** üzerinde bu agresifliği yapsaydın kasa **{best_asset['SON KASA']}** oluyordu!")
