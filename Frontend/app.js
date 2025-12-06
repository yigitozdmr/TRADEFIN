// Frontend/app.js - SAF JAVASCRIPT VERSİYONU (Login, Grafik, Abonelik)

const API_BASE_URL = 'http://127.0.0.1:5000';
// Proje Yönetimi için sabit kullanıcılar ve Ticker'lar (EPIC 4 gereksinimi)
const VALID_USERS = { 'admin': '12345', 'ekip1': 'sifre123' }; 
let userDB = { ...VALID_USERS };
// Modelin beklediği simülasyon verileri (EPIC 3'e gönderilecek)
const LAST_DAY_FEATURES = {
    Close: 105.5, Open: 104.0, High: 106.0, Low: 103.5, Volume: 500000, 
    MA_10: 103.0, RSI: 65.0
};
const TICKER_LIST = ["XU100", "GARAN", "KCHOL", "TUPRS", "EREGL", "THYAO"];


// --- 1. Uygulama Akışı ve Görünüm Yönetimi ---

function setView(viewId) {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard-screen').style.display = 'none';
    document.getElementById('subscription-screen').style.display = 'none';
    
    const targetElement = document.getElementById(viewId);
    if (targetElement) {
        targetElement.style.display = 'block';
    }
}

// --- 2. Giriş ve Kayıt İşlemleri (EPIC 4/Kullanıcı Yönetimi) ---

function renderLoginScreen(message = '') {
    document.getElementById('login-screen').innerHTML = `
        <h2 style="text-align:center; color:#4f89e9;">TRADEFIN Mobil Giriş</h2>
        <div id="login-message" style="color:red; margin-bottom:10px;">${message}</div>
        
        <div id="login-form-container">
            <h3>Giriş Yap</h3>
            <div class="form-group"><input type="text" id="login-username" placeholder="Kullanıcı Adı (admin)"></div>
            <div class="form-group"><input type="password" id="login-password" placeholder="Şifre (12345)"></div>
            <button class="btn-primary" onclick="handleLogin()">Giriş Yap</button>
            <p style="text-align:center; margin-top:15px;"><a href="#" onclick="renderRegisterScreen()" class="text-blue">Hesabın Yok Mu? Kayıt Ol</a></p>
            <p style="text-align:center; margin-top:15px;"><a href="#" onclick="renderSubscriptionScreen()" class="btn-primary" style="text-decoration:none;">Abonelikleri Gör</a></p>
        </div>
    `;
    setView('login-screen');
}

function renderRegisterScreen() {
    document.getElementById('login-screen').innerHTML = `
        <h2 style="text-align:center; color:#28a745;">Yeni Hesap Oluştur</h2>
        <div id="register-message" style="color:red; margin-bottom:10px;"></div>

        <p style="color:#aaaaaa;">**Prototip için sadece 'admin' / '12345' hesabı oluşturulabilir.**</p>
        <div class="form-group"><input type="text" id="reg-username" placeholder="Kullanıcı Adı (admin)"></div>
        <div class="form-group"><input type="password" id="reg-password" placeholder="Şifre (12345)"></div>
        <button class="btn-success" onclick="handleRegister()">Kayıt Ol</button>
        <p style="text-align:center; margin-top:15px;"><a href="#" onclick="renderLoginScreen()" class="text-blue">Zaten Hesabım Var</a></p>
    `;
}

window.handleRegister = function() {
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    
    if (username === 'admin' && password === '12345') {
        userDB[username] = { password: password };
        renderLoginScreen('<span style="color:#28a745;">Kayıt Başarılı! Şimdi Giriş Yapın.</span>');
    } else {
        document.getElementById('register-message').innerHTML = 'Sadece admin/12345 hesabı oluşturulabilir.';
    }
}

window.handleLogin = function() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const user = userDB[username];

    if (user && user.password === password) {
        renderDashboardScreen(); // Başarılı girişte Dashboard'a yönlendir
    } else {
        document.getElementById('login-message').innerHTML = 'Kullanıcı adı veya şifre hatalı.';
    }
}

// --- 3. Abonelik Sayfası (EPIC 4/Fiyatlandırma) ---

function renderSubscriptionScreen() {
    document.getElementById('subscription-screen').innerHTML = `
        <h2 style="color:#4f89e9; text-align:center;">Abonelik Planları</h2>
        <p style="text-align:right;"><a href="#" onclick="renderDashboardScreen()" class="btn-primary" style="text-decoration:none;">Ana Sayfa</a></p>
        
        <div class="metric" style="border: 2px solid #4f89e9;">
            <p class="metric-label">1 Aylık Plan</p>
            <p class="metric-value">299 TL</p>
            <p style="font-size:0.9em;">Tüm Hisseler, Temel Tahmin</p>
        </div>
        <div class="metric">
            <p class="metric-label">3 Aylık Plan</p>
            <p class="metric-value">399 TL</p>
            <p style="font-size:0.9em;">Gelişmiş Tahminler</p>
        </div>
        <div class="metric">
            <p class="metric-label">6 Aylık Plan</p>
            <p class="metric-value">599 TL</p>
            <p style="font-size:0.9em;">Öncelikli Destek</p>
        </div>
    `;
    setView('subscription-screen');
}


// --- 4. Dashboard, Grafik ve Tahmin (EPIC 4/Grafik & Tahmin) ---

function renderDashboardScreen(initialTicker = 'XU100') {
    document.getElementById('dashboard-screen').innerHTML = `
        <h1 style="color:#4f89e9; text-align:center;">TRADEFIN Dashboard</h1>
        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
            <p style="font-size:0.9em; color:#aaaaaa;">Giriş Yapan: Admin</p>
            <button class="btn-danger" onclick="renderLoginScreen()">Çıkış Yap</button>
        </div>

        <div class="form-group" style="margin-top:20px;">
            <label style="display:block; margin-bottom:5px;">Hisse Senedi Seçin:</label>
            <select id="ticker-select" onchange="updateDashboard(false, this.value)" style="width:100%;" class="form-group">
                ${TICKER_LIST.map(t => `<option value="${t}" ${t === initialTicker ? 'selected' : ''}>${t}.IS Hissesi</option>`).join('')}
            </select>
        </div>

        <button class="btn-success" style="width:100%;" onclick="updateDashboard(true)">Yarınki Fiyatı Tahmin Et</button>
        
        <p style="text-align:center; margin-top:20px;"><a href="#" onclick="renderSubscriptionScreen()" class="text-blue">Abonelik Planları</a></p>
        
        <div id="prediction-container" style="margin-top: 20px;"></div>
        <div id="info-container" style="margin-top: 20px; font-size:0.9em; color:#aaaaaa;"></div>

        <div class="chart-container"><canvas id="stockChart" height="300"></canvas></div> 

    `;
    setView('dashboard-screen');
    updateDashboard(false, initialTicker); // İlk yüklemede çalıştır
}

window.updateDashboard = async function(makePrediction = false, ticker = null) {
    const selectedTicker = ticker || document.getElementById('ticker-select').value;
    const predictionContainer = document.getElementById('prediction-container');
    const infoContainer = document.getElementById('info-container');
    
    // Şirket Tarihçesi ve Finansal Geçmiş (EPIC 4 gereksinimi)
    infoContainer.innerHTML = `<h3>${selectedTicker} Detayı</h3>
                               <p>Piyasada lider konumdadır. Finansal Geçmiş: Son çeyrekte net kar %15 artmıştır (Simülasyon).</p>`;

    predictionContainer.innerHTML = 'Yükleniyor...';

    // Grafik verisi simülasyonu
    const mockHistory = Array.from({ length: 50 }, (_, i) => ({
        date: `2024-11-${i + 1}`,
        price: 100 + (Math.sin(i / 10) * 10) + (TICKER_LIST.indexOf(selectedTicker) * 5)
    }));
    
    const lastPrice = mockHistory[mockHistory.length - 1].price;
    let predictedPrice = null;

    if (makePrediction) {
        // API'den Tahmin Çekme (EPIC 3 Bağlantısı)
        predictedPrice = await fetchPrediction(selectedTicker);
    }
    
    // Metrikleri ve Grafiği Güncelleme
    let metricsHTML = '';
    if (predictedPrice !== null && predictedPrice !== 0) {
        const change = predictedPrice - lastPrice;
        const changePercent = (change / lastPrice) * 100;
        const color = change > 0 ? '#1b5e20' : '#8b0000'; // Yeşil/Kırmızı arka plan

        // Tahmin ve Gün Sonu Değeri (EPIC 4 gereksinimi)
        metricsHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                <div class="metric">
                    <p class="metric-label">Son Kapanış</p>
                    <p class="metric-value">${lastPrice.toFixed(2)} ₺</p>
                </div>
                <div class="metric" style="background-color: ${color};">
                    <p class="metric-label">Tahmin Edilen Gün Sonu</p>
                    <p class="metric-value">${predictedPrice.toFixed(2)} ₺</p>
                </div>
                <div class="metric">
                    <p class="metric-label">Fark (%)</p>
                    <p class="metric-value" style="color:white;">${changePercent.toFixed(2)}%</p>
                </div>
            </div>
        `;

        // Grafiğe tahmin noktasını ekle
        mockHistory.push({ date: 'Yarın', price: predictedPrice, isPrediction: true });
    } else {
         metricsHTML = `<p style="margin-top:10px; color:#aaaaaa;">${makePrediction ? 'Tahmin alınamadı. API (port 5000) çalışıyor mu?' : 'Tahmin yapmak için yukarıdaki butona basınız.'}</p>`;
    }
    predictionContainer.innerHTML = metricsHTML;
    
    drawChart(mockHistory);
}

// API Bağlantısı (EPIC 3)
window.fetchPrediction = async function(ticker) {
    const payload = {
        Ticker: `${ticker}.IS`, 
        ...LAST_DAY_FEATURES 
    };

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            console.error(`API hatası: ${response.statusText}`);
            return null; 
        }

        const data = await response.json();
        return data.predicted_close;

    } catch (error) {
        console.error("Tahmin çekerken hata oluştu:", error);
        return null;