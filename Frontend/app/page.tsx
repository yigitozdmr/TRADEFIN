"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, Search, AlertCircle } from "lucide-react";

// --- TİP TANIMLAMALARI ---
interface FXRates {
  USD_TL: number | null;
  EUR_TL: number | null;
}

interface PredictionResult {
  ticker: string;
  predicted_close: number;
  prediction_date: string;
  kullanilan_usd_tl: number;
  current_price?: number; // Backend eklerse diye opsiyonel
}

export default function Home() {
  // --- STATE (DURUM) YÖNETİMİ ---
  const [ticker, setTicker] = useState("THYAO");
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [fxRates, setFxRates] = useState<FXRates>({ USD_TL: null, EUR_TL: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [longTermFx, setLongTermFx] = useState<any>(null);

  // --- 1. SAYFA YÜKLENİNCE ÇALIŞACAKLAR ---
  useEffect(() => {
    fetchFxRates();
    fetchLongTermFx();
  }, []);

  // --- API FONKSİYONLARI ---
  
  // 1. Anlık Döviz Kurlarını Çek
  const fetchFxRates = async () => {
    try {
      const res = await axios.get("http://localhost:5000/api/fx/current");
      setFxRates(res.data);
    } catch (err) {
      console.error("FX Hatası:", err);
    }
  };

  // 2. Uzun Vadeli Projeksiyonu Çek
  const fetchLongTermFx = async () => {
    try {
      const res = await axios.get("http://localhost:5000/api/fx/long_term");
      setLongTermFx(res.data);
    } catch (err) {
      console.error("Uzun Vade FX Hatası:", err);
    }
  };

  // 3. Hisse Tahmini ve Geçmiş Veri
  const handlePredict = async () => {
    setLoading(true);
    setError("");
    setPrediction(null);

    try {
      // A. Önce Geçmiş Veriyi Çek (Grafik İçin)
      const historyRes = await axios.get(`http://localhost:5000/api/history/${ticker}`);
      setHistoryData(historyRes.data);

      // B. Tahmin İsteği Gönder
      // NOT: Backend'in veri çekme mantığını güncellediğimiz varsayımıyla sadece Ticker gönderiyoruz.
      const predictRes = await axios.post("http://localhost:5000/api/predict", {
        Ticker: ticker
      });
      
      setPrediction(predictRes.data);

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error || "Tahmin sırasında bir hata oluştu. Backend bağlantısını kontrol edin.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      
      {/* --- HEADER --- */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Activity className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
              TRADEFIN
            </span>
          </div>
          
          {/* Döviz Göstergesi */}
          <div className="hidden md:flex items-center gap-6 text-sm font-medium">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-full border border-green-100">
              <DollarSign className="w-4 h-4" />
              <span>USD: {fxRates.USD_TL ? fxRates.USD_TL.toFixed(2) : "..."} ₺</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full border border-blue-100">
              <span>€</span>
              <span>EUR: {fxRates.EUR_TL ? fxRates.EUR_TL.toFixed(2) : "..."} ₺</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        
        {/* --- ANALİZ BÖLÜMÜ --- */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* SOL PANEL: GİRDİ VE SONUÇ */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* 1. Hisse Seçimi Kartı */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h2 className="text-lg font-semibold mb-4">Piyasa Analizi</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-600 mb-1">Hisse Kodu (BIST)</label>
                  <div className="relative">
                    <input 
                      type="text" 
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value.toUpperCase())}
                      className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                      placeholder="Örn: THYAO"
                    />
                    <Search className="w-5 h-5 text-slate-400 absolute left-3 top-3.5" />
                  </div>
                </div>
                
                <button 
                  onClick={handlePredict}
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? "Analiz Yapılıyor..." : "Yapay Zeka ile Analiz Et"}
                  {!loading && <Activity className="w-4 h-4" />}
                </button>

                {error && (
                  <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 mt-0.5" />
                    <p>{error}</p>
                  </div>
                )}
              </div>
            </div>

            {/* 2. Tahmin Sonucu Kartı */}
            {prediction && (
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                <h3 className="text-slate-500 text-sm font-medium mb-1">Yarın İçin Tahmin ({prediction.ticker})</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-4xl font-bold text-slate-900">{prediction.predicted_close} ₺</span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-2 border-b border-slate-50">
                    <span className="text-slate-500">Tahmin Tarihi</span>
                    <span className="font-medium">{prediction.prediction_date}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-50">
                    <span className="text-slate-500">Kullanılan Kur</span>
                    <span className="font-medium">{prediction.kullanilan_usd_tl} ₺</span>
                  </div>
                  <div className="mt-4 p-3 bg-indigo-50 text-indigo-700 rounded-lg text-xs">
                    * Bu tahmin yapay zeka tarafından teknik indikatörler ve kur verileri kullanılarak üretilmiştir.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* SAĞ PANEL: GRAFİKLER */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* 1. Hisse Fiyat Grafiği */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px]">
              <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-slate-400" />
                {ticker} Fiyat Geçmişi
              </h3>
              
              {historyData.length > 0 ? (
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={historyData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis 
                      dataKey="Date" 
                      tick={{fontSize: 12, fill: '#64748b'}} 
                      tickFormatter={(val) => val.slice(5)} 
                      stroke="#cbd5e1"
                    />
                    <YAxis 
                      domain={['auto', 'auto']} 
                      tick={{fontSize: 12, fill: '#64748b'}} 
                      stroke="#cbd5e1"
                    />
                    <Tooltip 
                      contentStyle={{backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="Close" 
                      stroke="#2563eb" 
                      strokeWidth={3} 
                      dot={false} 
                      activeDot={{r: 6}} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400">
                  Veri görüntülemek için analiz yapın.
                </div>
              )}
            </div>

            {/* 2. Uzun Vadeli Kur Projeksiyonu */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h3 className="text-lg font-semibold mb-4">2027 Uzun Vadeli Kur Projeksiyonu (CAGR)</h3>
              {longTermFx ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                    <p className="text-green-600 text-sm font-medium mb-1">Dolar (Yıllık Büyüme)</p>
                    <p className="text-2xl font-bold text-green-700">%{ (longTermFx.USD_CAGR * 100).toFixed(2) }</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                    <p className="text-blue-600 text-sm font-medium mb-1">Euro (Yıllık Büyüme)</p>
                    <p className="text-2xl font-bold text-blue-700">%{ (longTermFx.EUR_CAGR * 100).toFixed(2) }</p>
                  </div>
                </div>
              ) : (
                <p className="text-slate-400">Projeksiyon verisi yükleniyor...</p>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
} 