# Backend_API/app.py - DÜZELTİLMİŞ NİHAİ VERSİYON

from flask_cors import CORS
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from flask import Flask, request, jsonify
import joblib
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import numpy as np

app = Flask(__name__)
CORS(app) # Bu satır Frontend'in Backend ile konuşmasına izin verir

# --- 1. DOSYA YOLLARI (DİNAMİK HALE GETİRİLDİ) ---
# Bu dosyanın (app.py) bulunduğu klasörü al
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Bir üst klasöre çık (TRADEFIN ana klasörü)
BASE_DIR = os.path.dirname(CURRENT_DIR)

# Yolları birleştir
MODEL_DIR = os.path.join(BASE_DIR, "ML_Model")
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.joblib")
TICKER_MAP_PATH = os.path.join(MODEL_DIR, "ticker_mapping.joblib")
LONG_FX_MODEL_PATH = os.path.join(MODEL_DIR, "long_term_fx_model.joblib")

# --- 2. MODELLERİ YÜKLEME ---
stock_predictor = None
ticker_mapping = {}

try:
    if os.path.exists(MODEL_PATH):
        stock_predictor = joblib.load(MODEL_PATH)
        print("✅ API: Hisse Fiyat Modeli (Random Forest) yüklendi.")
    else:
        print(f"⚠️ UYARI: Model dosyası bulunamadı: {MODEL_PATH}")

    if os.path.exists(TICKER_MAP_PATH):
        ticker_mapping = joblib.load(TICKER_MAP_PATH)
        print("✅ API: Ticker Haritası yüklendi.")
except Exception as e:
    print(f"❌ API HATA: Model yüklenirken sorun oluştu: {e}")

# --- 3. YARDIMCI FONKSİYONLAR ---

def fetch_real_time_fx():
    """Anlık Dolar ve Euro kurlarını çeker (Yfinance MultiIndex Düzeltmesi ile)."""
    fx_tickers = ['USDTRY=X', 'EURTRY=X']
    try:
        # period='1d' son kapanışı getirir
        df = yf.download(fx_tickers, period="1d", progress=False)
        
        # Yfinance MultiIndex Düzeltmesi
        if isinstance(df.columns, pd.MultiIndex):
            # Sadece 'Close' fiyatlarını al ve ticker isimlerine indirge
            df = df.xs('Close', axis=1, level=0)
        elif 'Close' in df.columns:
             df = df['Close']
        
        # Son satırı al (Series döner)
        last_rates = df.iloc[-1]
        
        return {
            "USD_TL": float(last_rates.get('USDTRY=X', 0)),
            "EUR_TL": float(last_rates.get('EURTRY=X', 0))
        }
    except Exception as e:
        print(f"FX Çekme Hatası: {e}")
        return {"USD_TL": None, "EUR_TL": None}

def calculate_input_features(latest_data_series, fx_rates, ticker_encoded):
    """Tahmin için DataFrame hazırlar. Model eğitimiyle AYNI SIRADA olmalı."""
    input_features = {
        'Close': [latest_data_series.get('Close')],
        'Open': [latest_data_series.get('Open')],
        'High': [latest_data_series.get('High')],
        'Low': [latest_data_series.get('Low')],
        'Volume': [latest_data_series.get('Volume')],
        'MA_10': [latest_data_series.get('MA_10')],
        'RSI': [latest_data_series.get('RSI')],
        'Ticker_Encoded': [ticker_encoded],
        'USD_TL': [fx_rates['USD_TL']],
        'EUR_TL': [fx_rates['EUR_TL']]
    }
    return pd.DataFrame(input_features)

# --- 4. API UÇ NOKTALARI (ROUTES) ---

@app.route('/api/predict', methods=['POST'])
def predict_stock_price():
    if stock_predictor is None:
        return jsonify({"error": "Model sunucuda yüklü değil."}), 503

    data = request.get_json()
    ticker = data.get('Ticker') # Frontend sadece bunu gönderiyor

    if not ticker:
        return jsonify({"error": "Ticker parametresi zorunludur."}), 400

    try:
        # --- OTOMATİK VERİ TAMAMLAMA (FRONTEND İÇİN) ---
        # Frontend teknik verileri göndermiyorsa, biz çekelim
        symbol = f"{ticker}.IS"
        df = yf.download(symbol, period="1y", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            return jsonify({"error": "Hisse verisi bulunamadı."}), 404

        # Teknik İndikatörleri Hesapla (Modelin istediği formatta)
        df['RSI'] = RSIIndicator(close=df["Close"], window=14).rsi()
        df['MA_10'] = SMAIndicator(close=df["Close"], window=10).sma_indicator() # Model MA_10 istiyorsa
        
        last_row = df.iloc[-1]

        # Model girdilerini hazırla
        input_data_dict = {
            'Ticker': ticker,
            'Close': last_row['Close'],
            'Open': last_row['Open'],
            'High': last_row['High'],
            'Low': last_row['Low'],
            'Volume': last_row['Volume'],
            'MA_10': last_row.get('MA_10', last_row['Close']), # MA_10 yoksa Close kullan (Fallback)
            'RSI': last_row.get('RSI', 50) # RSI yoksa 50 kullan
        }
        
        # --- DEVAMI AYNI ---
        ticker_encoded = ticker_mapping.get(ticker, 0)
        
        fx_rates = fetch_real_time_fx()
        if fx_rates['USD_TL'] is None:
            fx_rates = {"USD_TL": 34.50, "EUR_TL": 36.50}

        input_df = calculate_input_features(input_data_dict, fx_rates, ticker_encoded)
        prediction = stock_predictor.predict(input_df)

        return jsonify({
            "ticker": ticker,
            "predicted_close": round(float(prediction[0]), 2),
            "prediction_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "kullanilan_usd_tl": round(fx_rates['USD_TL'], 2)
        })

    except Exception as e:
        print(f"Hata detayı: {e}")
        return jsonify({"error": f"Tahmin hatası: {str(e)}"}), 500
    
@app.route('/api/fx/current', methods=['GET'])
def get_current_fx():
    """Frontend Header'ı için anlık kurlar."""
    fx_rates = fetch_real_time_fx()
    if fx_rates['USD_TL'] is None:
        return jsonify({"error": "Kur verisi alınamadı"}), 500
        
    return jsonify({
        "USD_TL": round(fx_rates['USD_TL'], 4),
        "EUR_TL": round(fx_rates['EUR_TL'], 4)
    })

@app.route('/api/fx/long_term', methods=['GET'])
def get_long_term_fx():
    """Uzun vadeli FX projeksiyonu (Zaman çizelgesi veya spesifik tarih)."""
    try:
        fx_projections = joblib.load(LONG_FX_MODEL_PATH)
    except FileNotFoundError:
        return jsonify({"error": "Uzun vadeli FX modeli bulunamadı. Lütfen modeli eğitin."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    target_date_str = request.args.get('target_date')

    # SENARYO A: Spesifik bir tarih isteniyorsa
    if target_date_str:
        try:
            target_date = pd.to_datetime(target_date_str)
            start_date_str = fx_projections.get('PROJECTION_START_DATE') or fx_projections.get('PROJECTION_START')
            start_date = pd.to_datetime(start_date_str)
            
            # Kaydedilmiş son gerçek değerleri kullan (Daha hassas hesaplama için)
            # Eğer modelinizde 'LAST_USD_VALUE' yoksa timeline'ın ilk elemanını kullanırız
            last_usd = fx_projections.get('LAST_USD_VALUE', fx_projections['USD_TL_TIMELINE'][0]['Value'])
            last_eur = fx_projections.get('LAST_EUR_VALUE', fx_projections['EUR_TL_TIMELINE'][0]['Value'])
            
            usd_cagr = fx_projections['USD_CAGR']
            eur_cagr = fx_projections['EUR_CAGR']
            
            # Yıl farkı hesabı
            proj_years = (target_date - start_date).days / 365.25
            
            if proj_years < 0:
                return jsonify({"error": "Geçmiş bir tarih için tahmin yapılamaz."}), 400

            pred_usd = last_usd * ((1 + usd_cagr) ** proj_years)
            pred_eur = last_eur * ((1 + eur_cagr) ** proj_years)

            return jsonify({
                "tahmin_tarihi": target_date_str,
                "usd_tl_tahmini": round(pred_usd, 2),
                "eur_tl_tahmini": round(pred_eur, 2)
            })
        except Exception as e:
            return jsonify({"error": f"Hesaplama hatası: {str(e)}"}), 400

    # SENARYO B: Tüm zaman çizelgesi isteniyorsa (Grafik için)
    else:
        return jsonify({
            "USD_TL_Timeline": fx_projections['USD_TL_TIMELINE'],
            "EUR_TL_Timeline": fx_projections['EUR_TL_TIMELINE'],
            "baslangic_tarihi": fx_projections.get('PROJECTION_START_DATE'),
            # --- EKLENEN SATIRLAR ---
            "USD_CAGR": fx_projections.get('USD_CAGR', 0),
            "EUR_CAGR": fx_projections.get('EUR_CAGR', 0)
        })

@app.route('/api/history/<ticker>', methods=['GET'])
def get_history(ticker):
    """Grafik çizimi için son 90 günlük geçmiş."""
    try:
        symbol = f"{ticker}.IS"
        # Yfinance MultiIndex Düzeltmesi (history için)
        df = yf.download(symbol, period="3mo", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            return jsonify({"error": "Veri bulunamadı"}), 404
            
        # Tarihi string'e çevir ve listeye dönüştür
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        result = df[['Date', 'Close']].to_dict('records')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Geçmiş veri hatası: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Backend API Çalışıyor (Port 5000)...")
    app.run(debug=True, port=5000)