# Data_source/data_merger_fx.py
# ... (Başlangıçta importlar ve BASE_DIR tanımları aynı kalsın) ...

# Sütun adlarını tanımlama
doviz_kolonlari = ['USD_TL', 'EUR_TL']

def run_merger():
    print("\n--- data_merger_fx.py çalıştı ---")
    
    # 1. Döviz verisini yükleme (Bu kısım artık doğru çalışıyor)
    try:
        # ... doviz_data yükleme ve yeniden adlandırma kısmı ...
        
        # Sadece USD_TL ve EUR_TL kolonlarını tut
        doviz_data = doviz_data[doviz_kolonlari] 
        print(f"✅ Döviz verisi yüklendi. Sütunlar: {list(doviz_data.columns)}")
        
    except Exception as e:
        # ... hata işleme kısmı ...
        return
    
    # 2. İşlenmiş hisse senedi dosyalarını bulma (Bu kısım aynı)
    islenmis_dosyalar = glob.glob(os.path.join(PROCESSED_DIR, '*_processed.csv'))
    
    if not islenmis_dosyalar:
        # ... hata mesajı ...
        return

    for dosya_yolu in islenmis_dosyalar:
        
        dosya_adi = os.path.basename(dosya_yolu)
        hisse_kodu = dosya_adi.split('_')[0]
        
        print(f"➡️ {hisse_kodu} verisi döviz kurlarıyla birleştiriliyor...")
        
        hisse_data = pd.read_csv(dosya_yolu, index_col=0, parse_dates=True)

        # 🛑 KRİTİK DÜZELTME: Merge işlemi
        # Merge işlemi, doviz_data'daki kolonları hisse_data'ya ekler.
        birlestirilmis_data = hisse_data.merge(doviz_data, 
                                             left_index=True, 
                                             right_index=True, 
                                             how='left') 
        
        # Eksik Değerleri Doldurma (Şimdi bu kolonlar DAHA KESİN olarak var)
        # Eğer kolonlar hâlâ yoksa, merge başarısız olmuştur (tarih formatı uyuşmazlığı).
        try:
             birlestirilmis_data[doviz_kolonlari] = birlestirilmis_data[doviz_kolonlari].fillna(method='ffill')
        except KeyError as e:
             # Eğer buraya düşersek, tarih formatı uyuşmuyor demektir.
             print(f"🚨 KRİTİK HATA: Birleştirme sonrası USD/EUR kolonları hala eksik. Tarih indeksleri çakışmıyor! Detay: {e}")
             continue # Diğer dosyalara geç

        # Birleştirilen veriyi Processed_Data klasörüne yeni bir dosya olarak kaydetme
        yeni_dosya_adi = os.path.join(PROCESSED_DIR, f'{hisse_kodu}_final_processed.csv')
        birlestirilmis_data.to_csv(yeni_dosya_adi)
        
        print(f"   ✅ {hisse_kodu} verisi güncellendi ve kaydedildi: {os.path.basename(yeni_dosya_adi)}")


if __name__ == "__main__":
    run_merger()