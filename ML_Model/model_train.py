import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

# 1. TEK VE MERKEZİ VERİ HAZIRLAMA FONKSİYONU
def prepare_data(symbol):
    print(f"{symbol} için veri çekiliyor...")
    
    # Veriyi indir (Son 3 yıl)
    df = yf.download(symbol, period="3y", interval="1d")
    
    # --- YFINANCE FORMAT DÜZELTMESİ ---
    # Sütunlar MultiIndex (katmanlı) gelirse düzleştirir
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # ----------------------------------

    # Veri boşsa kontrol et
    if df.empty:
        raise ValueError("Veri boş geldi. Sembolü kontrol edin.")

    # --- ÖZNİTELİK MÜHENDİSLİĞİ (Feature Engineering) ---
    
    # RSI (14 gün)
    df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
    
    # MACD
    macd_indicator = MACD(close=df["Close"])
    df["MACD"] = macd_indicator.macd()
    
    # Hareketli Ortalamalar (SMA 20 ve SMA 50)
    # Not: SMA_50'yi feature listesinde kullandığınız için burada hesaplamalıyız.
    df["SMA_20"] = SMAIndicator(close=df["Close"], window=20).sma_indicator()
    df["SMA_50"] = SMAIndicator(close=df["Close"], window=50).sma_indicator()
    
    # HEDEF (Target) BELİRLEME
    # 'Prediction' sütunu, bir sonraki günün 'Close' fiyatıdır.
    df["Prediction"] = df["Close"].shift(-1)
    
    return df

# ANA AKIŞ
if __name__ == "__main__":
    symbol = "GARAN.IS" # Örnek hisse
    
    try:
        # 1. Veriyi Hazırla (İndikatörler ve Target dahil)
        full_data = prepare_data(symbol)
        
        # 2. Gelecek Tahmini İçin Son Satırı Ayır
        # Son satırın 'Prediction' değeri NaN'dır (çünkü yarın henüz olmadı).
        # Bu satırı eğitimden çıkarıp, en sonda "Yarın"ı tahmin etmek için saklıyoruz.
        features = ["RSI", "MACD", "SMA_20", "SMA_50", "Close"]
        
        # Gelecek tahmini için kullanılacak girdi (Bugünün kapanış verileri)
        X_future_input = full_data.iloc[[-1]][features] 
        
        # 3. Eğitim Verisini Temizle
        # İçinde NaN olan (ilk 50 gün ve son satır) verileri atıyoruz.
        data_clean = full_data.dropna()
        
        # Özellikler (X) ve Hedef (y)
        X = data_clean[features]
        y = data_clean["Prediction"]
        
        # 4. Eğitim ve Test Bölünmesi
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        # 5. Model Eğitimi
        print("Model eğitiliyor...")
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # 6. Test ve Değerlendirme
        predictions = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        mae = mean_absolute_error(y_test, predictions)
        
        print(f"Model Başarısı (RMSE): {rmse:.2f} TL")
        print(f"Ortalama Mutlak Hata (MAE): {mae:.2f} TL")
        
        # 7. GERÇEK ZAMANLI TAHMİN (YARIN İÇİN)
        future_prediction = model.predict(X_future_input)
        current_price = X_future_input["Close"].values[0]
        
        print(f"------------------------------------------------")
        print(f"{symbol} Mevcut Fiyat: {current_price:.2f} TL")
        print(f"Tahmin Edilen Yarınki Fiyat: {future_prediction[0]:.2f} TL")
        
        if future_prediction[0] > current_price:
            print("Yön: YUKARI 🔼 (Potansiyel Alış Fırsatı)")
        else:
            print("Yön: AŞAĞI 🔽 (Düşüş Beklentisi)")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")