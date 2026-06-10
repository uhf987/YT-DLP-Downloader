# ▶ YT-DLP İndirici

YouTube, Instagram, Twitter/X ve daha yüzlerce siteden video/ses indirmenizi sağlayan, kullanımı kolay masaüstü uygulaması.

---

## 🚀 Kurulum

### 1. Python
Python 3.8 veya üstü kurulu olmalıdır.
İndirme: https://www.python.org/downloads/

### 2. yt-dlp
CMD'yi açın ve şu komutu çalıştırın:
```
pip install yt-dlp
```

### 3. FFmpeg (birleştirme için gerekli)
Yüksek kaliteli video indirmek için FFmpeg gereklidir.
İndirme: https://ffmpeg.org/download.html
İndirdiğiniz `ffmpeg.exe` dosyasını sistem PATH'ine ekleyin
ya da yt-dlp ile aynı klasöre koyun.

---

## ▶ Çalıştırma

### Python ile:
```
python yt_dlp_gui.py
```

### EXE olarak derlemek için:
```
pip install pyinstaller
pyinstaller --onefile --noconsole --name "YT-DLP-Indirici" yt_dlp_gui.py
```
Derleme tamamlandığında `dist\YT-DLP-Indirici.exe` dosyası oluşur.

---

## 🖥️ Kullanım

### Temel Kullanım
1. Uygulamayı açın
2. İndirmek istediğiniz videonun linkini kopyalayın
3. Link otomatik olarak yapıştırılır ve indirme başlar

### ⚡ OTO Modu (varsayılan: açık)
- **Açık:** Herhangi bir `http://` veya `https://` linki kopyaladığınızda uygulama onu anında algılar, link kutusuna yapıştırır ve indirmeyi otomatik başlatır.
- **Kapalı:** Link yalnızca yapıştırılır; indirme için **İNDİR** butonuna basmanız gerekir.
- Bir indirme sürerken yeni link kopyalanırsa, mevcut indirme bitmeden yeni indirme başlamaz.

### 📌 ÜST Modu (varsayılan: kapalı)
- Butona tıklayınca pencere her zaman diğer pencerelerin üstünde sabitlenir.
- Tarayıcıda video ararken uygulama görünür kalmaya devam eder.
- Tekrar tıklayınca normal moda döner.

### YAPIŞTIR Butonu
- Panodaki linki manuel olarak link kutusuna yapıştırır.

### Kalite Seçimi
| Seçenek | Açıklama |
|---|---|
| best | Mevcut en yüksek kalite (varsayılan) |
| 1080p | Full HD, maksimum 1080p |
| 720p | HD, maksimum 720p |
| 480p | SD, maksimum 480p |
| ses only (mp3) | Yalnızca ses, MP3 formatında |

### Kayıt Klasörü
- Varsayılan olarak `İndirilenler` (Downloads) klasörüne kaydeder.
- **SEÇ** butonu ile istediğiniz klasörü belirleyebilirsiniz.

### Cookies Dosyası (opsiyonel)
Instagram, Twitter gibi giriş gerektiren siteler için gereklidir.

**Cookies dosyası nasıl alınır:**
1. Microsoft Edge veya Chrome'a **"Get cookies.txt LOCALLY"** eklentisini kurun
2. İlgili siteye giriş yapın
3. Eklentiyi açıp cookies.txt dosyasını kaydedin
4. Uygulamada **SEÇ** butonu ile bu dosyayı seçin

### Aynı İsimli Dosyalar
Aynı isimde dosya zaten varsa yeni dosya otomatik olarak `Video Adı (2).mp4`, `Video Adı (3).mp4` şeklinde adlandırılır. Mevcut dosyanıza dokunulmaz.

### ÇIKTI Paneli
- İndirme sürecini canlı olarak gösterir.
- **TEMİZLE** butonu ile log temizlenebilir.

---

## 🌐 Desteklenen Siteler

YouTube, Instagram, Twitter/X, TikTok, Facebook, Twitch, Vimeo, Dailymotion ve 1000+ site.
Tam liste: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

## ❓ Sık Karşılaşılan Sorunlar

**"yt-dlp bulunamadı" hatası**
→ `pip install yt-dlp` komutunu çalıştırın ve PATH ayarlarını kontrol edin.

**Instagram/Twitter indirmiyor**
→ Cookies dosyası gereklidir. Yukarıdaki adımları takip edin.

**Ses ve video birleşmiyor**
→ FFmpeg kurulu değil. Kurulum adımlarına bakın.

**Chrome/Edge açıkken cookies alınamıyor**
→ Tarayıcı açıkken çerez dosyası kilitlenir. Cookies.txt yöntemini kullanın.

---

## 📁 Dosya Yapısı

```
YT-DLP-Indirici/
├── yt_dlp_gui.py   → Uygulama kaynak kodu
└── README.md       → Bu dosya
```
