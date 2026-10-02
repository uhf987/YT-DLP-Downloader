# Video Sniffer + yt-dlp İndirici

Chrome'da oynayan videonun gerçek indirme bağlantısını yakalayan bir **Chrome eklentisi** ile bu bağlantıyı [yt-dlp](https://github.com/yt-dlp/yt-dlp) kullanarak indiren bir **masaüstü aracı**. İkisi birlikte, Internet Download Manager (IDM) gibi "videoyu oynat, tek tıkla indir" akışını sağlar.

yt-dlp'nin tanımadığı video sitelerinde bile işe yarar: eklenti sayfayı değil tarayıcının gerçek ağ trafiğini izlediği için, JavaScript ile sonradan oluşturulan video bağlantılarını da görür.

## Özellikler

**Chrome eklentisi**

- Oynatılan videonun `.mp4`, `.webm`, `.m3u8` (HLS) ve `.mpd` (DASH) isteklerini yakalar.
- Birden fazla sonuç arasından **tek bir "en iyi"** seçer. Öncelik sırası: HLS ana liste (içindeki en yüksek çözünürlükle), DASH manifest, en büyük video dosyası, HLS alt liste. Diğerleri "Diğer yakalananlar" altında durur.
- Çok küçük dosyaları (önizleme/reklam, 300 KB altı) eler.
- VK gibi sitelerde videoyu parça parça çeken `&bytes=` aralıklarını tek kayıtta birleştirir.
- Tarayıcının o istekte gönderdiği **Referer, Origin, User-Agent ve Cookie** başlıklarını da yakalar. Birçok CDN bunlar olmadan 403 verir, IDM'in linki tek başına yapıştırınca indirememesinin sebebi de budur.
- Tek tıkla **araca gönderir**, ya da link/komut olarak panoya kopyalar.

**Masaüstü aracı**

- yt-dlp için sade bir arayüz: kalite seçimi (best, 1080p, 720p, 480p, mp3), kayıt klasörü, cookies.txt desteği.
- Eklentiden gelen bağlantıyı başlıklarıyla birlikte indirir.
- Pano takibi: panoya kopyalanan `http(s)` bağlantısı kutuya otomatik yazılır. **OTO** düğmesi açıksa indirme de otomatik başlar (varsayılan olarak kapalı).
- Aynı isimde dosya varsa üzerine yazmaz, `(2)`, `(3)` ekler.
- **Sistem tepsisine küçültme**, indirme bitince bildirim.
- Instagram gibi yt-dlp'nin zaten desteklediği sitelerde düz link yapıştırınca eskisi gibi çalışır.

## Nasıl çalışır?

```
┌────────────────────┐   POST /add (link + başlıklar)   ┌──────────────────┐
│  Chrome eklentisi  │ ───────────────────────────────▶ │  Masaüstü aracı  │
│  (webRequest ile   │      http://127.0.0.1:8765       │  (Tkinter)       │
│   video yakalar)   │                                  │        │         │
└────────────────────┘                                  │        ▼         │
                                                        │      yt-dlp      │
                                                        └──────────────────┘
```

Araç açılırken yalnızca `127.0.0.1` üzerinde küçük bir HTTP sunucusu başlatır. Eklenti yakaladığı bağlantıyı ve başlıkları buraya gönderir, araç da bunları `--referer`, `--user-agent` ve `--add-header` olarak yt-dlp'ye verir.

## Gereksinimler

- Windows (araç ve paketleme Windows'ta denendi)
- Python 3.9 veya üstü
- [yt-dlp](https://github.com/yt-dlp/yt-dlp), PATH'te kurulu olmalı
- [ffmpeg](https://ffmpeg.org/), PATH'te kurulu olmalı (görüntü ve sesi birleştirmek, m3u8 indirmek için gerekir)
- Google Chrome (ya da Chromium tabanlı bir tarayıcı)
- Firefox, yalnızca çerez gerektiren sitelerde (aşağıya bak)
- İsteğe bağlı: tepsi simgesi için `pystray` ve `pillow`

## Kurulum

### 1. Masaüstü aracı

```
pip install pystray pillow
python yt_dlp_gui.py
```

`pystray` ve `pillow` kurulu değilse araç yine çalışır, yalnızca tepsiye küçültme devre dışı kalır.

### 2. Chrome eklentisi

1. `chrome://extensions` sayfasını aç.
2. Sağ üstten **Geliştirici modu**'nu aç.
3. **Paketlenmemiş öğe yükle** düğmesine bas ve `extension` klasörünü seç.

Eklenti dosyaları: `manifest.json`, `background.js`, `popup.html`, `popup.js`.

## Kullanım

1. Aracı aç. Çıktı kutusunda `🌐 Eklenti bağlantısı hazır (127.0.0.1:8765)` yazısını görmelisin.
2. Chrome'da videoyu **oynat** (eklenti, video oynarken yapılan istekleri yakalar).
3. Eklenti simgesine tıkla. Simgenin üstündeki rozet yakalanan istek sayısını gösterir.
4. Yeşil "★ En iyi" kutusundaki **Araca gönder** düğmesine bas. İndirme başlar.

Sayfa yenilenince liste temizlenir. Eklenti kurulduktan ya da güncellendikten sonra sayfayı yenileyip videoyu tekrar oynat.

### Eklenti düğmeleri

| Düğme | Ne yapar |
|---|---|
| **Araca gönder** | Link ve başlıkları doğrudan araca yollar, indirme başlar. |
| **Araca gönder (cookie ile)** | Aynısı, ayrıca tarayıcının çerezini de ekler. |
| **GUI için kopyala** | Panoya link + başlıkları koyar (aracın pano takibi bunu çözer). |
| **GUI (cookie ile)** | Aynısı, çerez dahil. |
| **URL kopyala** | Sadece linki kopyalar. |
| **yt-dlp komutu** | Terminalde çalıştırılabilir tam bir yt-dlp komutu kopyalar. |
| **yt-dlp komutu (cookie ile)** | Aynısı, çerez dahil. |

Önce cookie'siz düğmeleri dene. Çoğu sitede Referer, Origin ve User-Agent yeterlidir. 403 hatası alırsan cookie'li olanı kullan.

### Araca pano ile bağlantı verme

Eklenti olmadan da kullanabilirsin. Araç, panoya kopyalanan şu üç biçimi tanır:

- Düz link: `https://...`
- İlk satırı link, sonraki satırları `Referer: ...` gibi başlıklar olan metin ("GUI için kopyala" çıktısı)
- `yt-dlp --referer "..." "https://..."` biçiminde bir komut

### Araç arayüzü

- **⚡ OTO:** Açıksa panoya kopyalanan her `http(s)` bağlantısı hemen indirilmeye başlar. Varsayılan: kapalı.
- **📌 ÜST:** Pencereyi her zaman diğerlerinin üstünde tutar.
- **🗕 KÜÇÜLT:** Pencereyi sistem tepsisine alır. Simgeye tıklayınca geri gelir, sağ tık menüsünde "Göster" ve "Çıkış" var. Pencerenin X düğmesi programı kapatır.

### Çerezler

Araç çerez gereken sitelerde (Instagram gibi) varsayılan olarak **Firefox'un** çerezlerini okur (`--cookies-from-browser firefox`). Chrome ve Edge'in çerez şifrelemesi yüzünden yt-dlp onları güvenilir okuyamayabiliyor. Başka bir kaynak istersen arayüzdeki **COOKIES** alanından bir `cookies.txt` dosyası seçebilirsin, o zaman Firefox yerine o kullanılır.

## Exe olarak paketleme

```
python -m pip install pyinstaller pystray pillow
python -m PyInstaller --onefile --noconsole --name "YT-DLP Indirici" --icon icon.ico --hidden-import pystray._win32 yt_dlp_gui.py
```

Çıktı `dist\YT-DLP Indirici.exe` olarak oluşur. yt-dlp ve ffmpeg exe'nin içine girmez, kullanıcının bilgisayarında kurulu olmaları gerekir.

Notlar:

- `--noconsole` ile yapılan exe'lerde yt-dlp her çalıştığında siyah bir pencere açılmasın diye kod gizli pencere ayarıyla çalıştırılıyor.
- `--onefile` exe'leri bazen antivirüs tarafından yanlışlıkla şüpheli bulunur. Sorun olursa `--onedir` ile derle.

## Güvenlik

- Yerel sunucu yalnızca `127.0.0.1` adresinde dinler, dış ağdan erişilemez.
- `Origin` başlığı `chrome-extension://` ile başlamayan istekler ve beklenmeyen `Host` başlıklı istekler reddedilir. Yani başka bir web sitesi aracına indirme yaptıramaz.
- **Cookie'li** düğmeler oturum bilgini içeren metin üretir. Bunu başkalarıyla paylaşma, terminal geçmişinde de kalabileceğini unutma.
- Eklenti `<all_urls>` izniyle çalışır, çünkü videoyu hangi sitede açacağın önceden bilinmez. Yalnızca kendi bilgisayarında yerel olarak çalışır ve hiçbir veriyi dışarı göndermez.

## Sınırlamalar

- **DRM korumalı içerik** (Widevine vb., Netflix, Disney+ gibi) indirilemez.
- Bazı siteler bağlantıyı IP'ye ya da oturuma bağlar ve süreli yapar. Linki hemen kullanmak ve aracı eklentiyle aynı bilgisayarda/ağda çalıştırmak gerekir.
- Araç aynı anda **tek indirme** yapar. Meşgulken eklentiden gelen istek "Araç meşgul" diye reddedilir.
- Site yalnızca tek kalite alt listesi (`index-v1-a1.m3u8` gibi) sunuyorsa "en iyi" olarak o görünür. Böyle durumlarda "Diğer yakalananlar" listesine bak.
- Tepsi, çerez ve paketleme kısımları Windows için yazıldı.

## Sorun giderme

| Belirti | Olası sebep |
|---|---|
| Eklenti "Araç açık değil" diyor | Araç kapalı ya da 8765 portu başka bir program tarafından kullanılıyor. Aracın çıktı kutusunu kontrol et. |
| Eklenti "Henüz video isteği yakalanmadı" diyor | Videoyu oynatmadan popup'ı açtın ya da eklentiyi güncelledikten sonra sayfayı yenilemedin. |
| 403 / "Forbidden" hatası | Cookie'li düğmeyi dene. Link süresi dolmuş olabilir, videoyu yeniden oynatıp yeni link al. |
| `... is not a valid URL` | Eklentinin eski sürümü kullanılıyor olabilir. `popup.js`'i güncelleyip eklentiyi yenile. |
| Dosya 26 KB gibi küçük iniyor | Parça isteği (`&bytes=`) indirilmiş. Güncel eklenti bunu temizler, VK gibi sitelerde manifest (en iyi) linkini kullan. |
| `yt-dlp bulunamadı` | yt-dlp PATH'te değil. Kurulumu ve PATH'i kontrol et. |
| Görüntü var ses yok / birleştirme hatası | ffmpeg kurulu değil ya da PATH'te değil. |
| `pyinstaller` tanınmıyor | `pyinstaller` yerine `python -m PyInstaller` yaz. |

## Proje yapısı

```
.
├── yt_dlp_gui.py        # Masaüstü aracı (Tkinter + yerel sunucu + tepsi)
├── icon.ico             # Exe simgesi
└── extension/
    ├── manifest.json    # Chrome eklenti tanımı (Manifest V3)
    ├── background.js    # Ağ isteklerini ve başlıkları yakalar
    ├── popup.html       # Eklenti penceresi
    └── popup.js         # Liste, düğmeler ve araca gönderme
```

## Yasal uyarı

Bu araç yalnızca indirme hakkına sahip olduğun içerikler için, kişisel kullanım amacıyla hazırlanmıştır. İndirdiğin içeriklerin telif haklarına ve ilgili sitelerin kullanım koşullarına uymak senin sorumluluğundadır. Koruma altındaki (DRM) içerikleri aşmak için tasarlanmamıştır.

## Teşekkürler

- [yt-dlp](https://github.com/yt-dlp/yt-dlp), indirme işinin tamamını yapan proje
- [pystray](https://github.com/moses-palmer/pystray) ve [Pillow](https://python-pillow.org/), tepsi simgesi için

## Lisans

<!-- Buraya seçtiğin lisansı yaz (ör. MIT) ve depoya bir LICENSE dosyası ekle. -->
