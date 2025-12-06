import pandas as pd
import ta
import os
import glob

RAW_DATA_PATTERN = os.path.join("Data_source", "*_data.csv")
PROCESSED_DIR = os.path.join("Data_source", "Processed_Data")

if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)
    print(f"Klasör oluşturuldu: {PROCESSED_DIR}")

def read_stock_csv(path, ticker_name):
    """
    CSV dosyasını doğru şekilde okumaya çalışır.
    Bazı dosyalar 1, bazıları 2 header satırına sahip olabilir.
    """
    try:
        # Önce çift başlık olarak dene
        df = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
        # Eğer kolonlar tuple tipindeyse, sadece içteki isimleri al
        if isinstance(df.columns[0], tuple):
            df.columns = [c[0] for c in df.columns]
        return df
    except Exception:
        # Olmazsa tek header olarak dene
        df = pd.read_csv(path, header=1, index_col=0, parse_dates=True)
        return df

def preprocess_ticker_data(raw_file_path):
    file_name = os.path.basename(raw_file_path)
    ticker_name = file_name.replace("_data.csv", "")
    print(f"\n--- Ön İşleme Başladı: {ticker_name} ---")

    try:
        df = read_stock_csv(raw_file_path, ticker_name)
    except Exception as e:
        print(f"HATA: {ticker_name} dosyası okunurken hata: {e}")
        return

    # Şimdi sütun isimlerini doğru sırada ayarla
    # Bazı dosyalarda Adj Close olabilir, bazılarında olmayabilir
    columns = [col.lower() for col in df.columns]
    possible_sets = [
        ["open", "high", "low", "close", "adj close", "volume"],
        ["open", "high", "low", "close", "volume"],
        ["close", "high", "low", "open", "volume", "adj close"],
        ["price", "high", "low", "open", "close", "volume"]
    ]

    matched = False
    for pattern in possible_sets:
        if all(p in columns for p in pattern):
            df.columns = [c.capitalize() for c in pattern]
            matched = True
            break

    if not matched:
        print(f"HATA: {ticker_name} beklenmedik kolon yapısı: {df.columns}")
        return

    # Tüm sütunları numerik yap
    df = df.apply(pd.to_numeric, errors='coerce')
    df.dropna(inplace=True)

    # Teknik göstergeler
    try:
        df['MA_10'] = ta.trend.sma_indicator(df['Close'], window=10, fillna=False)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14, fillna=False)
        df['Target_Close'] = df['Close'].shift(-1)
        df.dropna(inplace=True)
    except Exception as e:
        print(f"HATA: {ticker_name} indikatör hesaplanamadı: {e}")
        return

    processed_path = os.path.join(PROCESSED_DIR, f"{ticker_name}_processed.csv")
    df.to_csv(processed_path)
    print(f"✅ {ticker_name} tamamlandı | {len(df)} satır | Kaydedildi: {processed_path}")

if __name__ == "__main__":
    print("data_preprocess.py çalıştı 🚀")

    all_files = glob.glob(RAW_DATA_PATTERN)

    if not all_files:
        print("HATA ❌: Hiçbir ham veri bulunamadı. Lütfen önce data_fetch.py'yi çalıştır.")
    else:
        for f in all_files:
            preprocess_ticker_data(f)

        print("\n=== ✅ TÜM VERİ SETLERİ BAŞARIYLA ÖN İŞLENDİ. ML MODEL AŞAMASINA GEÇİLEBİLİR. ===")