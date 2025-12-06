# ML_Model/model_train.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import os
import glob
import joblib 

# NİHAİ YOL DÜZELTMESİ: Betiğin bulunduğu yerden mutlak yolu hesapla
# Bu yol, ML_Model'den bir seviye yukarı (..) çıkarak Data_source/Processed_Data klasörüne gider.
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data_source', 'Processed_Data')
MODEL_PATH = "ML_Model/random_forest_model.joblib"

def load_and_combine_data():
    """Tüm ön işlenmiş veri setlerini okur ve tek bir DataFrame'de birleştirir."""
    
    # Processed_Data klasöründeki tüm CSV dosyalarını bul
    all_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*_processed.csv"))
    
    if not all_files:
        print(f"HATA: Processed_Data klasöründe hiç ön işlenmiş veri bulunamadı! Yol kontrolü: {PROCESSED_DATA_DIR}")
        return None
        
    all_data = []
    
    for file_path in all_files:
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        # Hangi hisseye ait olduğunu belirtmek için Ticker ekle
        df['Ticker'] = os.path.basename(file_path).split('_')[0]
        all_data.append(df)
        
    combined_df = pd.concat(all_data)
    print(f"Tüm veriler birleştirildi. Toplam satır: {len(combined_df)}")
    return combined_df

def train_and_save_model(data_df):
    """Random Forest modelini eğitir ve kaydeder."""

    # Ticker sütununu sayısal kategoriye dönüştür
    data_df['Ticker_Encoded'] = data_df['Ticker'].astype('category').cat.codes

    # 1. Özellikleri (X) ve Hedefi (Y) Belirleme
    features = [
        'Close', 'Open', 'High', 'Low', 'Volume', 
        'MA_10', 'RSI', 'Ticker_Encoded'
    ]
    target = 'Target_Close'
    
    X = data_df[features]
    Y = data_df[target]

    # 2. Eğitim ve Test Kümelerine Ayırma
    split_point = int(len(X) * 0.80)
    X_train, X_test = X[:split_point], X[split_point:]
    Y_train, Y_test = Y[:split_point], Y[split_point:]
    
    print(f"Eğitim seti boyutu: {len(X_train)}, Test seti boyutu: {len(X_test)}")

    # 3. Random Forest Modelini Eğitme
    print("Model eğitimi başlıyor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, Y_train)
    print("Model eğitimi tamamlandı.")

    # 4. Performansı Değerlendirme
    predictions = model.predict(X_test)
    mse = mean_squared_error(Y_test, predictions)
    r2 = r2_score(Y_test, predictions)

    print(f"\n--- Model Performansı ---")
    print(f"Hata Kare Ortalaması (MSE): {mse:.2f}")
    print(f"R-Kare Skoru (R2): {r2:.2f}")

    # 5. Modeli Kaydetme
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel başarıyla kaydedildi: {MODEL_PATH}")
    
    # Modelin kullandığı Ticker kodlamasını da kaydedelim (Backend için kritik)
    ticker_mapping = data_df[['Ticker', 'Ticker_Encoded']].drop_duplicates().set_index('Ticker').to_dict()['Ticker_Encoded']
    joblib.dump(ticker_mapping, 'ML_Model/ticker_mapping.joblib')

if __name__ == "__main__":
    combined_data = load_and_combine_data()
    if combined_data is not None:
        train_and_save_model(combined_data)