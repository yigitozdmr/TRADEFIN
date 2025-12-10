# ML_Model/long_term_fx_model.py - NİHAİ VERSİYON (CAGR PROJEKSİYONU)

import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

# --- PATH AYARLARI ---
# BASE_DIR: Projenin ana klasörüne (TRADEFIN) ulaşır
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_SOURCE_PATH = os.path.join(BASE_DIR, 'Data_source', 'dolar_euro_kurlari.csv')
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'long_term_fx_model.joblib')

# --- PROJEKSİYON FONKSİYONLARI ---

def calculate_projection_timeline(fx_data_series: pd.Series, target_date_str='2027-12-31', freq='Q'):
    """
    Verilen kur serisine göre CAGR hesaplar ve hedef tarihe kadar projeksiyon yapar.
    :param fx_data_series: Tarih indeksi olan pandas Serisi (örn: fx_data['USD_TL'])
    :param target_date_str: Projeksiyonun biteceği tarih (YYYY-MM-DD)
    :param freq: Projeksiyon sıklığı ('Q': Çeyreklik, 'A': Yıllık, 'M': Aylık)
    :return: Projeksiyon listesi ve CAGR oranı
    """
    fx_data_series = fx_data_series.dropna()
    if len(fx_data_series) < 2:
        return [], 0.0

    start_value = fx_data_series.iloc[0]
    end_value = fx_data_series.iloc[-1]
    
    start_date = fx_data_series.index.min()
    end_date = fx_data_series.index.max()
    
    # 365.25 kullanarak artık yılları hesaba katma
    time_delta = (end_date - start_date).days
    num_years = time_delta / 365.25

    # 1. Bileşik Yıllık Büyüme Oranını (CAGR) Hesaplama
    # Hata kontrolü: Sıfıra bölme veya negatif değerden kök alma olmamalı
    if num_years <= 0 or start_value <= 0:
        cagr_rate = 0.0
    else:
        cagr_rate = ((end_value / start_value) ** (1 / num_years)) - 1
    
    # 2. Projeksiyon için Tarih Aralıklarını Belirleme
    target_date = pd.to_datetime(target_date_str)
    
    # Son veri tarihinden bir gün sonrası ile hedef tarih aralığını oluşturma
    start_point = end_date + timedelta(days=1)
    
    # Tarih aralığını oluştururken hedef tarihin dahil olduğundan emin olmak için inclusive='right' kullanılır.
    future_dates = pd.date_range(start=start_point, end=target_date, freq=freq, inclusive='right')
    
    projections = []
    
    for date in future_dates:
        # Son veri tarihinden projeksiyon tarihine kadar geçen yıl sayısı
        proj_years = (date - end_date).days / 365.25
        
        # Projeksiyon değeri (CAGR formülünün ileriye dönük kullanımı)
        projected_value = end_value * ((1 + cagr_rate) ** proj_years)
        
        projections.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Value': round(projected_value, 4)
        })
        
    return projections, cagr_rate

def train_long_term_fx_model():
    print("➡️ Uzun Vadeli FX Modeli Eğitimi Başlıyor (Zaman Çizelgesi Projeksiyonu)...")
    
    try:
        # Tarih sütununu indeks olarak ve tarih formatında oku
        fx_data = pd.read_csv(DATA_SOURCE_PATH, index_col=0, parse_dates=True)
    except FileNotFoundError:
        print(f"HATA: FX Veri dosyası bulunamadı: {DATA_SOURCE_PATH}")
        return

    # Projeksiyonları hesaplama
    usd_timeline, usd_cagr = calculate_projection_timeline(fx_data['USD_TL'])
    eur_timeline, eur_cagr = calculate_projection_timeline(fx_data['EUR_TL'])
    
    # Sonuçları API'nin kolayca yükleyeceği bir sözlük içinde kaydetme
    result_data = {
        'USD_TL_TIMELINE': usd_timeline,
        'EUR_TL_TIMELINE': eur_timeline,
        'USD_CAGR': round(usd_cagr, 4),
        'EUR_CAGR': round(eur_cagr, 4),
        'PROJECTION_START_DATE': fx_data.index.max().strftime('%Y-%m-%d'),
        'LAST_USD_VALUE': round(fx_data['USD_TL'].iloc[-1], 4),
        'LAST_EUR_VALUE': round(fx_data['EUR_TL'].iloc[-1], 4)
    }
    
    joblib.dump(result_data, MODEL_SAVE_PATH)
    
    print(f"✅ Uzun Vadeli FX Projeksiyonu zaman çizelgesi olarak kaydedildi.")
    print(f"   USD/TL (CAGR): {result_data['USD_CAGR']*100:.2f}%")
    
    # Projeksiyonların son değerlerini kontrol amaçlı yazdır
    if eur_timeline:
        print(f"   EUR/TL Projeksiyon Bitiş Değeri (2027 Sonu): {eur_timeline[-1]['Value']:.2f} TL")
    
if __name__ == "__main__":
    train_long_term_fx_model()