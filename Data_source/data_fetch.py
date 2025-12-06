# Data_Source/data_fetch.py - TÜM BIST HİSSE HAVUZU

import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# Tüm BIST verilerini çekmek istediğimiz hisseler
TICKER_LIST = [
    "XU100.IS",    # BIST 100 Endeksi
    "GARAN.IS",    # Garanti BBVA
    "KCHOL.IS",    # Koç Holding
    "TUPRS.IS",    # Tüpraş
    "EREGL.IS",    # Ereğli Demir Çelik
    "THYAO.IS"     # Türk Hava Yolları
]

START_DATE = "2010-01-01"
END_DATE = datetime.now().strftime('%Y-%m-%d')

def fetch_and_save_bist_data(ticker, start_date=START_DATE, end_date=END_DATE):
    """
    Belirtilen Borsa İstanbul (BIST) koduna ait tarihi verileri çeker ve kaydeder.
    """
    print(f"[{ticker}] verileri {start_date} tarihinden itibaren çekiliyor...")
    
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        
        if data.empty:
            print(f"HATA: {ticker} için veri çekilemedi veya veri seti boş.")
            return None

        # Veriyi bir CSV dosyasına kaydetme
        file_name = f"{ticker.replace('.', '_')}_data.csv"
        file_path = os.path.join("Data_source", file_name)
        data.to_csv(file_path)
        
        print(f"[{ticker}] Veri çekme başarılı. Toplam {len(data)} satır veri çekildi.")
        
        return data

    except Exception as e:
        print(f"Hata oluştu [{ticker}]: {e}")
        return None

# Ana işlev: Tüm hisseleri çekip kaydedelim
if __name__ == "__main__":
    
    for ticker in TICKER_LIST:
        fetch_and_save_bist_data(ticker)
        print("-" * 50)
    
    print("Tüm BIST havuzu verileri çekildi. Ön işleme aşamasına geçilebilir.")