import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os

# ── Renkler & Font ──────────────────────────────────────────────
BG       = "#0f0f0f"
CARD     = "#1a1a1a"
ACCENT   = "#ff4444"
ACCENT2  = "#ff6b35"
TEXT     = "#f0f0f0"
MUTED    = "#666666"
SUCCESS  = "#44ff88"
BORDER   = "#2a2a2a"
PIN_ON   = "#ffcc00"

FONT_TITLE  = ("Consolas", 22, "bold")
FONT_LABEL  = ("Consolas", 10)
FONT_BTN    = ("Consolas", 11, "bold")
FONT_LOG    = ("Consolas", 9)
FONT_SMALL  = ("Consolas", 8)

DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp İndirici")
        self.geometry("680x600")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.download_dir  = tk.StringVar(value=DEFAULT_DIR)
        self.quality       = tk.StringVar(value="best")
        self.cookies       = tk.StringVar(value="")
        self._last_clipboard = ""
        self._is_downloading = False
        self._auto_dl    = tk.BooleanVar(value=True)   # otomatik indir
        self._always_top = tk.BooleanVar(value=False)  # her zaman üstte
        self._build()
        self._poll_clipboard()

    # ── Arayüz ─────────────────────────────────────────────────
    def _build(self):
        # Başlık + pin butonu
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x", padx=30)
        tk.Label(hdr, text="▶  YT-DLP", font=FONT_TITLE,
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="  İndirici", font=FONT_TITLE,
                 fg=TEXT, bg=BG).pack(side="left")

        # Sağ üst kontroller
        ctrl = tk.Frame(hdr, bg=BG)
        ctrl.pack(side="right")

        # Otomatik indir toggle
        self.btn_auto = tk.Button(
            ctrl, text="⚡ OTO", font=FONT_SMALL,
            bg=ACCENT, fg="white", activebackground=ACCENT2,
            activeforeground="white", bd=0, cursor="hand2",
            padx=8, pady=5, command=self._toggle_auto
        )
        self.btn_auto.pack(side="left", padx=(0, 6))

        # Her zaman üstte pin butonu
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
            self, text="⬇  İNDİR", font=FONT_BTN,
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
        tk.Label(card, text="KAYIT KLASÖRü", font=FONT_LABEL,
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
        tk.Label(ck, text="COOKIES DOSYASI (opsiyonel)", font=FONT_LABEL,
                 fg=MUTED, bg=CARD).pack(anchor="w")
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
        self.log.tag_config("ok",  foreground=SUCCESS)
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

    # ── Yardımcılar ────────────────────────────────────────────
    def _paste(self):
        try:
            self.url_var.set(self.clipboard_get())
        except Exception:
            pass

    def _poll_clipboard(self):
        """Her 500ms'de panoyu kontrol et; yeni link varsa yapıştır ve gerekirse indir."""
        try:
            text = self.clipboard_get().strip()
            if text != self._last_clipboard:
                self._last_clipboard = text
                if text.startswith("http://") or text.startswith("https://"):
                    self.url_var.set(text)
                    # Otomatik indir açıksa ve şu an indirme yoksa başlat
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

    # ── İndirme ────────────────────────────────────────────────
    def _format_args(self, q):
        fmt = {
            "best":           "bestvideo+bestaudio/best",
            "1080p":          "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p":           "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p":           "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "ses only (mp3)": "bestaudio/best",
        }.get(q, "bestvideo+bestaudio/best")
        if q == "ses only (mp3)":
            return ["-x", "--audio-format", "mp3"]
        return ["-f", fmt]

    def _get_filename(self, url, q, ck):
        out = os.path.join(self.download_dir.get(), "%(title)s.%(ext)s")
        cmd = ["yt-dlp", "--print", "filename", "--simulate", "-o", out]
        cmd += self._format_args(q)
        if ck:
            cmd += ["--cookies", ck]
        cmd.append(url)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace"
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

        q  = self.quality.get()
        ck = self.cookies.get().strip()

        self._is_downloading = True
        self.btn_dl.config(state="disabled", text="⏳  İNDİRİLİYOR...")
        self._write_log("▶ Dosya adı kontrol ediliyor...\n", "inf")

        def run():
            try:
                predicted = self._get_filename(url, q, ck)
                if predicted:
                    unique = self._unique_path(predicted)
                    if unique != predicted:
                        self.after(0, self._write_log,
                            f"📋 Mevcut dosya var → {os.path.basename(unique)}\n", "inf")
                    out_path = unique
                else:
                    out_path = os.path.join(self.download_dir.get(), "%(title)s.%(ext)s")

                self.after(0, self._write_log, "▶ İndirme başlıyor...\n\n", "inf")

                cmd = ["yt-dlp"] + self._format_args(q)
                cmd += ["-o", out_path]
                if ck:
                    cmd += ["--cookies", ck]
                cmd.append(url)

                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace"
                )
                for line in proc.stdout:
                    tag = "ok"  if ("[download]" in line or "Destination" in line) \
                         else "err" if "ERROR" in line else ""
                    self.after(0, self._write_log, line, tag)
                proc.wait()

                if proc.returncode == 0:
                    self.after(0, self._write_log, "\n✅ İndirme tamamlandı!\n", "ok")
                else:
                    self.after(0, self._write_log, "\n❌ İndirme başarısız.\n", "err")

            except FileNotFoundError:
                self.after(0, self._write_log,
                           "❌ yt-dlp bulunamadı! PATH'e eklenmiş mi?\n", "err")
            finally:
                self._is_downloading = False
                self.after(0, lambda: self.btn_dl.config(
                    state="normal", text="⬇  İNDİR"))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
