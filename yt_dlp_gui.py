import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import shlex
import shutil
import sys
import queue
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Sistem tepsisi desteği (pip install pystray pillow)
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

# exe (--noconsole) olarak çalışırken yt-dlp için konsol penceresi açılmasın
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# Bu programın başlattığı alt süreçlere işaret koyulur. Yanlışlıkla program
# kendi kendini başlatırsa (yt-dlp yerine) hemen kapanır, pencere açmaz.
GUARD_VAR = "YTDLP_GUI_CHILD"
CHILD_ENV = dict(os.environ, **{GUARD_VAR: "1"})


def find_ytdlp():
    """
    PATH içinde yt-dlp'yi bulur ve TAM YOLUNU döndürür.
    Uygulamanın kendi exe'sini (adı yt-dlp.exe olsa bile) asla seçmez.
    Windows'un 'uygulama klasörü / çalışma klasörü önce aranır' davranışına
    güvenmemek için komut adı yerine tam yol kullanılır.
    """
    me = os.path.abspath(sys.executable)
    if os.name == "nt":
        names = ["yt-dlp.exe", "yt-dlp.cmd", "yt-dlp.bat"]
    else:
        names = ["yt-dlp"]
    for d in os.environ.get("PATH", "").split(os.pathsep):
        d = d.strip().strip('"')
        if not d:
            continue
        for n in names:
            p = os.path.join(d, n)
            if not os.path.isfile(p):
                continue
            try:
                if os.path.samefile(p, me):
                    continue
            except OSError:
                pass
            return p
    return None


def make_icon_image(size=64):
    """Tepsi simgesi: kırmızı yuvarlak kare içinde beyaz oynat üçgeni."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), radius=14, fill=(255, 68, 68, 255))
    d.polygon([(24, 18), (24, 46), (48, 32)], fill=(255, 255, 255, 255))
    return img.resize((size, size)) if size != 64 else img

# ── Renkler & Font ──────────────────────────────────────────────
BG = "#0f0f0f"
CARD = "#1a1a1a"
ACCENT = "#ff4444"
ACCENT2 = "#ff6b35"
TEXT = "#f0f0f0"
MUTED = "#666666"
SUCCESS = "#44ff88"
BORDER = "#2a2a2a"
PIN_ON = "#ffcc00"

FONT_TITLE = ("Consolas", 22, "bold")
FONT_LABEL = ("Consolas", 10)
FONT_BTN = ("Consolas", 11, "bold")
FONT_LOG = ("Consolas", 9)
FONT_SMALL = ("Consolas", 8)

DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Eklentinin gönderebildiği başlıklar
KNOWN_HEADERS = ("referer", "origin", "user-agent", "cookie")

# Eklenti ile haberleşen yerel sunucu (sadece bu bilgisayardan erişilebilir)
SERVER_PORT = 8765

# İndirme hızı modları: (yt-dlp -N parça sayısı, aria2c kullanılsın mı)
#  -N  : HLS/DASH (m3u8/mpd) parçalarını aynı anda N bağlantıyla indirir
#  aria2c : düz dosyaları (mp4 vb.) çok bağlantıyla bölerek indirir, IDM'e en yakın yöntem
SPEED_MODES = {
    "Normal (tek bağlantı)": (1, False),
    "Hızlı (8 parça aynı anda)": (8, False),
    "Çok hızlı (16 parça + aria2c varsa)": (16, True),
}
SPEED_DEFAULT = "Hızlı (8 parça aynı anda)"


def make_handler(app):
    """Eklentiden gelen istekleri alan HTTP işleyicisi."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # konsolu kirletme

        def _allowed(self):
            # DNS rebinding'e karşı Host kontrolü
            host = self.headers.get("Host", "")
            if host not in (f"127.0.0.1:{SERVER_PORT}", f"localhost:{SERVER_PORT}"):
                return False
            # Web siteleri Origin başlığını taklit edemez: sadece eklenti ya da
            # tarayıcı dışı yerel istemciler (Origin yok) kabul edilir
            origin = self.headers.get("Origin", "")
            return origin == "" or origin.startswith("chrome-extension://")

        def _send(self, code, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            origin = self.headers.get("Origin", "")
            if origin.startswith("chrome-extension://"):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            if not self._allowed():
                return self._send(403, {"ok": False, "error": "forbidden"})
            self._send(200, {"ok": True})

        def do_GET(self):
            if not self._allowed():
                return self._send(403, {"ok": False, "error": "forbidden"})
            if self.path == "/ping":
                return self._send(200, {"ok": True, "busy": app._is_downloading})
            self._send(404, {"ok": False, "error": "not found"})

        def do_POST(self):
            if not self._allowed():
                return self._send(403, {"ok": False, "error": "forbidden"})
            if self.path != "/add":
                return self._send(404, {"ok": False, "error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > 64 * 1024:
                    return self._send(400, {"ok": False, "error": "bad size"})
                data = json.loads(self.rfile.read(n).decode("utf-8"))
                url = str(data.get("url", "")).strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    return self._send(400, {"ok": False, "error": "bad url"})
                headers = {}
                for k, v in (data.get("headers") or {}).items():
                    if str(k).lower() in KNOWN_HEADERS and isinstance(v, str) and v:
                        headers[str(k)] = v
            except Exception:
                return self._send(400, {"ok": False, "error": "bad request"})

            if app._is_downloading:
                return self._send(409, {"ok": False, "error": "busy"})
            app._jobs.put((url, headers))
            self._send(200, {"ok": True})

    return Handler


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp İndirici")
        self.geometry("680x660")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.download_dir = tk.StringVar(value=DEFAULT_DIR)
        self.quality = tk.StringVar(value="best")
        self.cookies = tk.StringVar(value="")
        self.speed = tk.StringVar(value=SPEED_DEFAULT)
        self._last_clipboard = ""
        self._is_downloading = False
        self._auto_dl = tk.BooleanVar(value=False)      # otomatik indir (varsayılan KAPALI)
        self._always_top = tk.BooleanVar(value=False)   # her zaman üstte

        # Eklentiden gelen ekstra başlıklar (sadece o URL için geçerli)
        self._hdrs = {}
        self._hdrs_url = ""

        # Eklenti sunucusundan gelen işler
        self._jobs = queue.Queue()

        # Tepsi simgesi (başka iş parçacıklarından gelen arayüz komutları)
        self._tray = None
        self._ui_q = queue.Queue()
        self.protocol("WM_DELETE_WINDOW", self._quit)

        self._build()
        self._start_server()
        self._poll_clipboard()
        self._poll_jobs()
        self._poll_ui()

    # ── Arayüz ─────────────────────────────────────────────────
    def _build(self):
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x", padx=30)

        tk.Label(hdr, text="▶ YT-DLP", font=FONT_TITLE,
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" İndirici", font=FONT_TITLE,
                 fg=TEXT, bg=BG).pack(side="left")

        ctrl = tk.Frame(hdr, bg=BG)
        ctrl.pack(side="right")

        self.btn_tray = tk.Button(
            ctrl, text="🗕 KÜÇÜLT", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=ACCENT,
            activeforeground="white", bd=0, cursor="hand2",
            padx=8, pady=5, command=self._to_tray
        )
        self.btn_tray.pack(side="left", padx=(0, 6))

        # OTO varsayılan olarak kapalı başlar
        self.btn_auto = tk.Button(
            ctrl, text="⚡ OTO", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=ACCENT2,
            activeforeground="white", bd=0, cursor="hand2",
            padx=8, pady=5, command=self._toggle_auto
        )
        self.btn_auto.pack(side="left", padx=(0, 6))

        self.btn_pin = tk.Button(
            ctrl, text="📌 ÜST", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=PIN_ON,
            activeforeground="black", bd=0, cursor="hand2",
            padx=8, pady=5, command=self._toggle_pin
        )
        self.btn_pin.pack(side="left")

        self._card_link()
        self._card_settings()

        self.btn_dl = tk.Button(
            self, text="⬇ İNDİR", font=FONT_BTN,
            bg=ACCENT, fg="white", activebackground=ACCENT2,
            activeforeground="white", bd=0, cursor="hand2",
            padx=0, pady=12, command=self._start_download
        )
        self.btn_dl.pack(fill="x", padx=30, pady=(4, 10))

        self._card_log()

        tk.Label(self, text="yt-dlp sistemde kurulu olmalıdır",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(pady=(0, 8))

    def _card_link(self):
        card = tk.Frame(self, bg=CARD, bd=0, pady=14, padx=20)
        card.pack(fill="x", padx=30, pady=(0, 8))

        tk.Label(card, text="VIDEO BAĞLANTISI", font=FONT_LABEL,
                 fg=MUTED, bg=CARD).pack(anchor="w")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(6, 0))

        self.url_var = tk.StringVar()
        self.entry = tk.Entry(
            row, textvariable=self.url_var, font=FONT_LABEL,
            bg="#252525", fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=8
        )
        self.entry.pack(side="left", fill="x", expand=True)

        tk.Button(
            row, text="YAPIŞTIR", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=ACCENT,
            activeforeground="white", bd=0, cursor="hand2",
            padx=10, pady=8, command=self._paste
        ).pack(side="left", padx=(6, 0))

    def _card_settings(self):
        card = tk.Frame(self, bg=CARD, pady=14, padx=20)
        card.pack(fill="x", padx=30, pady=(0, 8))

        tk.Label(card, text="KAYIT KLASÖRÜ", font=FONT_LABEL,
                 fg=MUTED, bg=CARD).pack(anchor="w")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(4, 10))

        tk.Entry(
            row, textvariable=self.download_dir, font=FONT_LABEL,
            bg="#252525", fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=8
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            row, text="SEÇ", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=ACCENT,
            activeforeground="white", bd=0, cursor="hand2",
            padx=10, pady=8, command=self._choose_dir
        ).pack(side="left", padx=(6, 0))

        row2 = tk.Frame(card, bg=CARD)
        row2.pack(fill="x")

        ql = tk.Frame(row2, bg=CARD)
        ql.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Label(ql, text="KALİTE", font=FONT_LABEL,
                 fg=MUTED, bg=CARD).pack(anchor="w")
        ttk.Combobox(
            ql, textvariable=self.quality, font=FONT_LABEL,
            state="readonly", width=18,
            values=["best", "1080p", "720p", "480p", "ses only (mp3)"]
        ).pack(anchor="w", pady=(4, 0))

        ck = tk.Frame(row2, bg=CARD)
        ck.pack(side="left", expand=True, fill="x")
        tk.Label(ck, text="COOKIES (boşsa Firefox'tan otomatik alınır)",
                 font=FONT_LABEL, fg=MUTED, bg=CARD).pack(anchor="w")
        crow = tk.Frame(ck, bg=CARD)
        crow.pack(fill="x", pady=(4, 0))
        tk.Entry(
            crow, textvariable=self.cookies, font=FONT_LABEL,
            bg="#252525", fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=8, width=22
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            crow, text="SEÇ", font=FONT_SMALL,
            bg=BORDER, fg=MUTED, activebackground=ACCENT,
            activeforeground="white", bd=0, cursor="hand2",
            padx=8, pady=8, command=self._choose_cookies
        ).pack(side="left", padx=(4, 0))

        row3 = tk.Frame(card, bg=CARD)
        row3.pack(fill="x", pady=(10, 0))
        tk.Label(row3, text="İNDİRME HIZI (IDM gibi parçalı indirme)",
                 font=FONT_LABEL, fg=MUTED, bg=CARD).pack(anchor="w")
        ttk.Combobox(
            row3, textvariable=self.speed, font=FONT_LABEL,
            state="readonly", width=44, values=list(SPEED_MODES.keys())
        ).pack(anchor="w", pady=(4, 0))

    def _card_log(self):
        card = tk.Frame(self, bg=CARD, pady=10, padx=14)
        card.pack(fill="both", expand=True, padx=30, pady=(0, 6))

        header = tk.Frame(card, bg=CARD)
        header.pack(fill="x")
        tk.Label(header, text="ÇIKTI", font=FONT_LABEL,
                 fg=MUTED, bg=CARD).pack(side="left")
        tk.Button(header, text="TEMİZLE", font=FONT_SMALL,
                  bg=BORDER, fg=MUTED, bd=0, cursor="hand2",
                  padx=6, pady=2,
                  command=lambda: self.log.config(state="normal") or
                  self.log.delete("1.0", "end") or
                  self.log.config(state="disabled")
                  ).pack(side="right")

        self.log = tk.Text(
            card, font=FONT_LOG, bg="#111111", fg="#aaaaaa",
            relief="flat", bd=0, state="disabled",
            height=9, wrap="word"
        )
        self.log.pack(fill="both", expand=True, pady=(6, 0))
        self.log.tag_config("ok", foreground=SUCCESS)
        self.log.tag_config("err", foreground=ACCENT)
        self.log.tag_config("inf", foreground="#aaaaff")

    # ── Toggle'lar ─────────────────────────────────────────────
    def _toggle_auto(self):
        self._auto_dl.set(not self._auto_dl.get())
        if self._auto_dl.get():
            self.btn_auto.config(bg=ACCENT, fg="white", text="⚡ OTO")
        else:
            self.btn_auto.config(bg=BORDER, fg=MUTED, text="⚡ OTO")

    def _toggle_pin(self):
        self._always_top.set(not self._always_top.get())
        if self._always_top.get():
            self.attributes("-topmost", True)
            self.btn_pin.config(bg=PIN_ON, fg="black", text="📌 ÜST")
        else:
            self.attributes("-topmost", False)
            self.btn_pin.config(bg=BORDER, fg=MUTED, text="📌 ÜST")

    # ── Sistem tepsisi ─────────────────────────────────────────
    def _to_tray(self):
        if not HAS_TRAY:
            messagebox.showinfo(
                "Tepsi desteği yok",
                "Tepsiye küçültmek için şunu kurmalısın:\n\n"
                "pip install pystray pillow")
            return
        if self._tray is None:
            menu = pystray.Menu(
                pystray.MenuItem("Göster", lambda: self._ui_q.put(("show", "")),
                                 default=True),
                pystray.MenuItem("Çıkış", lambda: self._ui_q.put(("quit", ""))),
            )
            self._tray = pystray.Icon(
                "ytdlp_indirici", make_icon_image(), "yt-dlp İndirici", menu)
            self._tray.run_detached()
        self.withdraw()

    def _from_tray(self):
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
            self._tray = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit(self):
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
            self._tray = None
        self.destroy()

    def _poll_ui(self):
        """Tepsi menüsünden ve indirme iş parçacığından gelen komutlar."""
        try:
            while True:
                cmd, arg = self._ui_q.get_nowait()
                if cmd == "show":
                    self._from_tray()
                elif cmd == "quit":
                    self._quit()
                    return
                elif cmd == "notify" and self._tray is not None:
                    try:
                        self._tray.notify(arg, "yt-dlp İndirici")
                    except Exception:
                        pass
        except queue.Empty:
            pass
        self.after(200, self._poll_ui)

    # ── Eklenti sunucusu ───────────────────────────────────────
    def _start_server(self):
        try:
            self._server = ThreadingHTTPServer(
                ("127.0.0.1", SERVER_PORT), make_handler(self))
            threading.Thread(target=self._server.serve_forever,
                             daemon=True).start()
            self._write_log(
                f"🌐 Eklenti bağlantısı hazır (127.0.0.1:{SERVER_PORT})\n", "inf")
        except OSError:
            self._server = None
            self._write_log(
                f"⚠ {SERVER_PORT} portu kullanımda, eklentiden gönderme çalışmaz. "
                "Aracın başka bir kopyası açık olabilir.\n", "err")

    def _poll_jobs(self):
        """Eklentiden 'Araca gönder' ile gelen işleri al ve indir."""
        if not self._is_downloading:
            try:
                url, hdrs = self._jobs.get_nowait()
                self._set_url(url, hdrs)
                self._start_download()
            except queue.Empty:
                pass
        self.after(300, self._poll_jobs)

    # ── Pano / başlık ayrıştırma ───────────────────────────────
    def _parse_clip(self, text):
        """
        Pano metnini (url, başlıklar) olarak ayırır.
        Düz link  -> (link, {})            (eski davranışla aynı)
        Eklenti   -> ilk satır link, sonraki satırlar 'Referer: ...' gibi.
        'yt-dlp ...' komutu da çözülür.
        http ile başlamıyorsa (None, {}) döner.
        """
        text = text.strip()

        if text.startswith("yt-dlp "):
            return self._parse_command(text)

        if not (text.startswith("http://") or text.startswith("https://")):
            return None, {}

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) == 1:
            return lines[0], {}

        headers = {}
        for l in lines[1:]:
            name, sep, val = l.partition(":")
            if sep and name.strip().lower() in KNOWN_HEADERS:
                headers[name.strip()] = val.strip()
        return lines[0], headers

    def _parse_command(self, text):
        """'yt-dlp --referer "..." ... "URL"' metninden (url, başlıklar) çıkarır."""
        try:
            toks = shlex.split(text)
        except ValueError:
            return None, {}

        url = None
        headers = {}
        i = 1
        while i < len(toks):
            t = toks[i]
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if t == "--referer":
                headers["Referer"] = nxt
                i += 2
            elif t == "--user-agent":
                headers["User-Agent"] = nxt
                i += 2
            elif t == "--add-header":
                name, sep, val = nxt.partition(":")
                if sep and name.strip().lower() in KNOWN_HEADERS:
                    headers[name.strip()] = val.strip()
                i += 2
            elif t.startswith(("http://", "https://")):
                url = t
                i += 1
            else:
                i += 1
        if not url:
            return None, {}
        return url, headers

    def _set_url(self, url, headers):
        self.url_var.set(url)
        self._hdrs = headers
        self._hdrs_url = url if headers else ""

    def _header_args(self, url):
        """Başlıklar sadece eklentiden gelen URL ile aynı URL için kullanılır."""
        if not self._hdrs or url != self._hdrs_url:
            return []
        args = []
        for name, val in self._hdrs.items():
            n = name.lower()
            if n == "referer":
                args += ["--referer", val]
            elif n == "user-agent":
                args += ["--user-agent", val]
            else:
                args += ["--add-header", f"{name}: {val}"]
        return args

    # ── Yardımcılar ────────────────────────────────────────────
    def _paste(self):
        try:
            url, hdrs = self._parse_clip(self.clipboard_get())
            if url:
                self._set_url(url, hdrs)
            else:
                self._set_url(self.clipboard_get(), {})
        except Exception:
            pass

    def _poll_clipboard(self):
        """Her 500ms'de panoyu kontrol et; yeni link varsa yapıştır ve gerekirse indir."""
        try:
            raw = self.clipboard_get()
            text = raw.strip()
            if text != self._last_clipboard:
                self._last_clipboard = text
                url, hdrs = self._parse_clip(text)
                if url:
                    self._set_url(url, hdrs)
                    if self._auto_dl.get() and not self._is_downloading:
                        self._start_download()
        except Exception:
            pass
        self.after(500, self._poll_clipboard)

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.download_dir.get())
        if d:
            self.download_dir.set(d)

    def _choose_cookies(self):
        f = filedialog.askopenfilename(
            filetypes=[("Text/cookies", "*.txt"), ("Tümü", "*.*")]
        )
        if f:
            self.cookies.set(f)

    def _write_log(self, text, tag=""):
        self.log.config(state="normal")
        self.log.insert("end", text, tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _unique_path(self, path):
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 2
        while True:
            candidate = f"{base} ({i}){ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    def _cookie_args(self, ck):
        """
        Kullanıcı elle bir cookies.txt seçtiyse onu kullan.
        Seçmediyse, otomatik olarak Firefox tarayıcısının çerezlerini kullan.
        Firefox, Chrome/Edge'deki App-Bound Encryption korumasını
        kullanmadığı için yt-dlp çerezleri hiçbir eklentiye gerek
        kalmadan doğrudan okuyabilir.
        """
        if ck:
            return ["--cookies", ck]
        return ["--cookies-from-browser", "firefox"]

    # ── İndirme ────────────────────────────────────────────────
    def _format_args(self, q):
        fmt = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "ses only (mp3)": "bestaudio/best",
        }.get(q, "bestvideo+bestaudio/best")
        if q == "ses only (mp3)":
            return ["-x", "--audio-format", "mp3"]
        return ["-f", fmt]

    def _speed_args(self):
        """
        Seçilen hız moduna göre yt-dlp argümanları ve log mesajı döndürür.
        -N: HLS/DASH parçalarını paralel indirir (m3u8/mpd için asıl hızlandırma).
        aria2c: PATH'te varsa düz dosyaları çok bağlantıyla indirir; m3u8/mpd
        için yt-dlp'nin kendi indiricisi kalır (daha güvenilir).
        """
        n, want_aria = SPEED_MODES.get(self.speed.get(), SPEED_MODES[SPEED_DEFAULT])
        if n <= 1:
            return [], "Hız: normal (tek bağlantı)"
        args = ["-N", str(n)]
        msg = f"Hız: {n} parça aynı anda"
        if want_aria:
            aria = shutil.which("aria2c")
            if aria:
                args += ["--downloader", "aria2c",
                         "--downloader", "dash,m3u8:native",
                         "--downloader-args", "aria2c:-x16 -s16 -k1M"]
                msg += " + aria2c (düz dosyalar için)"
            else:
                msg += " (aria2c bulunamadı, sadece parçalı indirme)"
        return args, msg

    def _get_filename(self, ytdlp, url, q, ck, hdr_args):
        out = os.path.join(self.download_dir.get(), "%(title)s.%(ext)s")
        cmd = [ytdlp, "--ignore-config", "--print", "filename",
               "--simulate", "-o", out]
        cmd += self._format_args(q)
        cmd += self._cookie_args(ck)
        cmd += hdr_args
        cmd.append(url)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, creationflags=NO_WINDOW,
                env=CHILD_ENV
            )
            for l in reversed(result.stdout.strip().splitlines()):
                l = l.strip()
                if l and not l.startswith("["):
                    return l
        except Exception:
            pass
        return None

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir bağlantı girin.")
            return
        if self._is_downloading:
            return

        q = self.quality.get()
        ck = self.cookies.get().strip()
        hdr_args = self._header_args(url)   # düz linklerde boş liste
        speed_args, speed_msg = self._speed_args()

        ytdlp = find_ytdlp()
        if not ytdlp:
            self._write_log(
                "❌ yt-dlp bulunamadı! PATH'te yt-dlp.exe olmalı "
                "(bu programın kendi exe'si sayılmaz).\n", "err")
            return
        self._write_log(f"🔧 yt-dlp: {ytdlp}\n", "inf")
        self._write_log(f"⚡ {speed_msg}\n", "inf")

        self._is_downloading = True
        self.btn_dl.config(state="disabled", text="⏳ İNDİRİLİYOR...")
        self._write_log("▶ Dosya adı kontrol ediliyor...\n", "inf")
        if hdr_args:
            names = ", ".join(self._hdrs.keys())
            self._write_log(f"🔑 Eklentiden gelen başlıklar kullanılıyor: {names}\n", "inf")

        def run():
            try:
                predicted = self._get_filename(ytdlp, url, q, ck, hdr_args)
                if predicted:
                    unique = self._unique_path(predicted)
                    if unique != predicted:
                        self.after(0, self._write_log,
                                   f"📋 Mevcut dosya var → {os.path.basename(unique)}\n", "inf")
                    out_path = unique
                else:
                    out_path = os.path.join(self.download_dir.get(), "%(title)s.%(ext)s")

                self.after(0, self._write_log, "▶ İndirme başlıyor...\n\n", "inf")

                cmd = [ytdlp, "--ignore-config"] + self._format_args(q)
                cmd += ["-o", out_path]
                cmd += self._cookie_args(ck)
                cmd += hdr_args
                cmd += speed_args
                cmd.append(url)

                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, creationflags=NO_WINDOW,
                    env=CHILD_ENV,
                    text=True, encoding="utf-8", errors="replace"
                )
                for line in proc.stdout:
                    tag = "ok" if ("[download]" in line or "Destination" in line) \
                        else "err" if "ERROR" in line else ""
                    self.after(0, self._write_log, line, tag)
                proc.wait()

                if proc.returncode == 0:
                    self.after(0, self._write_log, "\n✅ İndirme tamamlandı!\n", "ok")
                    self._ui_q.put(("notify", "✅ İndirme tamamlandı"))
                else:
                    if proc.returncode == 3:
                        self.after(0, self._write_log,
                                   "\n⚠ yt-dlp yerine bu programın kendisi çalıştı. "
                                   "Exe'nin adı 'yt-dlp.exe' olmasın ve PATH'teki "
                                   "yt-dlp.exe'yi kontrol et.\n", "err")
                    self.after(0, self._write_log, "\n❌ İndirme başarısız.\n", "err")
                    self._ui_q.put(("notify", "❌ İndirme başarısız"))
            except FileNotFoundError:
                self.after(0, self._write_log,
                           "❌ yt-dlp bulunamadı! PATH'e eklenmiş mi?\n", "err")
            finally:
                self._is_downloading = False
                self.after(0, lambda: self.btn_dl.config(
                    state="normal", text="⬇ İNDİR"))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    # Program yanlışlıkla kendi alt süreci olarak başlatıldıysa pencere açma
    if os.environ.get(GUARD_VAR):
        sys.exit(3)
    app = App()
    app.mainloop()
