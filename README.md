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
İndirdiğiniz `ffmpeg.exe` dosyasını sistem PATH'ine ekleyin ya da yt-dlp ile aynı klasöre koyun.

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

> `pyinstaller` komutu "not recognized" hatası verirse, PATH sorunu vardır. Bunun yerine:
> ```
> python -m PyInstaller --onefile --noconsole --name "YT-DLP-Indirici" yt_dlp_gui.py
> ```

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

| Seçenek        | Açıklama                             |
| -------------- | ------------------------------------ |
| best           | Mevcut en yüksek kalite (varsayılan) |
| 1080p          | Full HD, maksimum 1080p              |
| 720p           | HD, maksimum 720p                    |
| 480p           | SD, maksimum 480p                    |
| ses only (mp3) | Yalnızca ses, MP3 formatında         |

### Kayıt Klasörü

- Varsayılan olarak `İndirilenler` (Downloads) klasörüne kaydeder.
- **SEÇ** butonu ile istediğiniz klasörü belirleyebilirsiniz.

### 🍪 Cookies (giriş gerektiren siteler için)

Instagram, Twitter gibi giriş gerektiren siteler için çerez (cookie) gereklidir. İki yöntem var:

**Yöntem 1 — Otomatik (önerilen, eklenti gerektirmez)**

Cookies kutusunu **boş bırakın**. Uygulama, hiçbir dosya seçilmemişse otomatik olarak **Firefox** tarayıcısının çerezlerini kullanır.

- Firefox'ta ilgili siteye (Instagram/Twitter vb.) giriş yapmış olmanız yeterlidir.
- Firefox açık kalabilir, kapatmanıza gerek yoktur.
- Chrome/Edge yerine Firefox tercih edilme sebebi: Chrome/Edge'in yeni sürümleri "App-Bound Encryption" adlı bir korumayla çerezleri şifreliyor ve bu, tarayıcı dışındaki hiçbir programın (yt-dlp dahil) çerezleri okumasına izin vermiyor. Firefox bu korumayı kullanmadığı için otomatik okuma sorunsuz çalışır.

**Yöntem 2 — Manuel dosya seçimi**

1. Herhangi bir tarayıcıya **"Get cookies.txt LOCALLY"** gibi bir eklenti kurun
2. İlgili siteye giriş yapın
3. Eklentiyi açıp cookies.txt dosyasını dışa aktarın (export)
4. Uygulamada **SEÇ** butonu ile bu dosyayı seçin

> Not: cookies.txt dosyasını Not Defteri ile elle düzenlerseniz, dosyayı **UTF-8** kodlamasıyla kaydedin. Aksi halde `'utf-8' codec can't decode byte` hatası alabilirsiniz.

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

**"yt-dlp bulunamadı" hatası** → `pip install yt-dlp` komutunu çalıştırın ve PATH ayarlarını kontrol edin.

**"pyinstaller is not recognized" hatası** → `pyinstaller` yerine `python -m PyInstaller ...` komutunu kullanın.

**Instagram/Twitter indirmiyor** → Cookies gereklidir. Firefox'ta giriş yapıp cookies kutusunu boş bırakın, ya da manuel cookies.txt seçin.

**`ERROR: Failed to decrypt with DPAPI`** → Bu hata, çerezleri Chrome/Edge'den otomatik okumaya çalışırken alınır. Modern Chrome/Edge sürümleri "App-Bound Encryption" kullandığı için bu artık mümkün değil. Firefox kullanın ya da manuel cookies.txt yöntemine geçin.

**Ses ve video birleşmiyor** → FFmpeg kurulu değil. Kurulum adımlarına bakın.

**Manuel cookies.txt kullanırken "utf-8 codec" hatası** → Dosyayı Not Defteri'nde "Farklı Kaydet" ile UTF-8 kodlamasında yeniden kaydedin.

---

## 📁 Dosya Yapısı

```
YT-DLP-Indirici/
├── yt_dlp_gui.py   → Uygulama kaynak kodu
└── README.md       → Bu dosya
```
