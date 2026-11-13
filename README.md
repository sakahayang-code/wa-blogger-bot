# 🤖 WhatsApp AI Blogger Auto-Post Bot (Python)

Bot WhatsApp otomatis berbasis **Python** dan **Google Gemini Flash AI** untuk menghasilkan artikel blog berkualitas tinggi, lengkap dengan gambar thumbnail otomatis, dan langsung diterbitkan ke blog Blogger/Blogspot ber-template **Median UI**.

---

## 🌟 Fitur Utama

* **🚫 Tanpa Node.js:** 100% Python murni (FastAPI), sangat ringan, efisien, dan hemat RAM.
* **⚡ Aktif 24 Jam Penuh (Gratis):** Didesain khusus agar bisa di-deploy gratis 24 jam non-stop di cloud (Render, Koyeb, atau VPS) langsung dari repositori GitHub Anda.
* **🎨 Dioptimalkan Khusus untuk Template Median UI:**
  * Menghasilkan struktur HTML rapi (`<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`).
  * Menyertakan kotak alert tips khas Median UI (`<div class="alert alert-info">`).
  * Menyertakan blok Tanya Jawab (FAQ) terstruktur.
* **🖼️ Thumbnail Otomatis:**
  * Men-generate gambar ilustrasi 16:9 beresolusi tinggi menggunakan **Google Imagen 3** (dengan fallback cerdas).
  * Gambar disisipkan di baris paling atas artikel, sehingga tema Median UI otomatis mengenali dan memasangnya sebagai **Featured Thumbnail / Cover** di beranda blog.
* **🔒 Bebas Masalah Token Expired:**
  * Memanfaatkan fitur resmi **Mail-to-Blogger** via SMTP Gmail. Sekali setup, berjalan selamanya tanpa perlu memperbarui Google Cloud OAuth token setiap beberapa hari.
* **🛡️ Fitur Keamanan Owner:**
  * Anda bisa mengunci bot agar hanya nomor WhatsApp Anda yang bisa memerintahkan penulisan artikel (`OWNER_NUMBER`).

---

## 🏗️ Struktur Proyek

```
wa-blogger-bot/
├── config.py                 # Pengaturan konfigurasi & environment variable
├── main.py                   # Server FastAPI, endpoint webhook WA & background task
├── services/
│   ├── gemini_service.py     # Generator artikel SEO & thumbnail Imagen 3
│   ├── blogger_service.py    # Pengirim postingan ke Blogger via SMTP
│   └── whatsapp_service.py   # Pengirim balasan notifikasi ke WhatsApp
├── requirements.txt          # Dependensi Python
├── Procfile                  # Konfigurasi start server di Render/Railway
├── render.yaml               # Blueprint auto-deploy 1-klik di Render.com
├── Dockerfile                # Opsi deploy container
├── .env.example              # Template variabel konfigurasi
└── README.md                 # Dokumentasi panduan lengkap
```

---

## 🚀 Panduan Setup Langkah Demi Langkah

### Langkah 1: Dapatkan Google Gemini API Key
1. Buka [Google AI Studio](https://aistudio.google.com/).
2. Masuk dengan akun Google Anda.
3. Klik tombol **Get API key** > **Create API key**.
4. Salin kunci API yang didapatkan (awalan `AIzaSy...`).

### Langkah 2: Aktifkan Fitur Mail-to-Blogger
1. Buka dashboard [Blogger](https://www.blogger.com/).
2. Masuk ke menu **Setelan (Settings)** > scroll ke bawah ke bagian **Email**.
3. Klik **Publikasikan postingan menggunakan email**.
4. Pilih opsi **Publikasikan email segera** (atau *Simpan email sebagai draf* jika Anda ingin meninjaunya dulu sebelum terbit).
5. Masukkan kata kunci rahasia (contoh: `artikelku123`).
6. Alamat email Blogger Anda akan menjadi: `namabloganda.artikelku123@blogger.com`. Simpan alamat ini untuk variabel `BLOGGER_EMAIL`.

### Langkah 3: Buat Password Aplikasi Gmail (App Password)
Agar bot bisa mengirim email ke alamat Blogger di atas dengan aman:
1. Masuk ke [Keamanan Akun Google](https://myaccount.google.com/security).
2. Pastikan **Verifikasi 2 Langkah (2FA)** di akun Google Anda sudah AKTIF.
3. Buka halaman [Sandi Aplikasi (App Passwords)](https://myaccount.google.com/apppasswords).
4. Buat sandi baru:
   * Nama aplikasi: `Blogger Bot`
5. Google akan memberikan **16 karakter kode sandi** (misal: `abcd efgh ijkl mnop`). Simpan ini untuk `GMAIL_APP_PASSWORD`.

### Langkah 4: Siapkan WhatsApp Gateway (Fonnte - Gratis)
1. Buka [Fonnte.com](https://fonnte.com/) dan daftar akun gratis.
2. Di dashboard Fonnte, scan QR Code menggunakan WhatsApp di ponsel Anda (*Perangkat Tertaut*).
3. Salin **API Token Fonnte** Anda untuk variabel `FONNTE_TOKEN`.

---

## ☁️ Cara Deploy 24 Jam Non-Stop di Render.com (Gratis)

1. **Push proyek ini ke Repositori GitHub Anda:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit bot wa blogger"
   git remote add origin https://github.com/USERNAME_ANDA/NAMA_REPO.git
   git push -u origin main
   ```
2. Buka [Render.com](https://render.com/) dan klik **Sign In with GitHub**.
3. Klik tombol **New +** > pilih **Web Service**.
4. Pilih repositori GitHub Anda tadi.
5. Konfigurasi dasar:
   * **Name:** `wa-blogger-bot`
   * **Language:** `Python 3`
   * **Region:** `Singapore` (Paling cepat dari Indonesia)
   * **Branch:** `main`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   * **Instance Type:** `Free`
6. Scroll ke bawah ke bagian **Environment Variables** dan tambahkan:
   * `GEMINI_API_KEY` : (API Key dari Langkah 1)
   * `GEMINI_MODEL` : `gemini-2.5-flash`
   * `BLOGGER_EMAIL` : (Email rahasia Blogger dari Langkah 2)
   * `GMAIL_USER` : (Alamat email Gmail Anda)
   * `GMAIL_APP_PASSWORD` : (Sandi aplikasi 16 karakter dari Langkah 3)
   * `FONNTE_TOKEN` : (Token dari Langkah 4)
   * `OWNER_NUMBER` : `628xxxxxxxxxx` (Nomor WhatsApp Anda, tanpa +)
7. Klik **Create Web Service**.
8. Dalam 1-2 menit, Render akan memberikan URL publik untuk bot Anda (misal: `https://wa-blogger-bot-xxxx.onrender.com`).

### Langkah 5: Pasang Webhook di Fonnte
1. Kembali ke dashboard [Fonnte.com](https://fonnte.com/).
2. Masuk ke menu **Device** > pilih perangkat Anda.
3. Di kolom **Webhook URL**, masukkan URL dari Render tadi ditambah `/webhook`:
   ```
   https://wa-blogger-bot-xxxx.onrender.com/webhook
   ```
4. Simpan pengaturan. Selesai! Bot Anda sekarang online 24 jam non-stop!

---

## 📱 Cara Menggunakan dari WhatsApp

Kirim pesan ke nomor WhatsApp yang terhubung:

| Perintah | Fungsi | Contoh |
| :--- | :--- | :--- |
| `!tulis <topik>` | Otomatis membuat & memposting artikel + thumbnail | `!tulis cara merawat baterai smartphone agar awet bertahun-tahun` |
| `!status` | Mengecek apakah server online dan koneksi Blogger siap | `!status` |
| `!menu` | Menampilkan panduan dan petunjuk perintah | `!menu` |

---

## 🧪 Menguji Secara Lokal (Opsional di Laptop/PC)

1. Salin `.env.example` menjadi `.env` lalu lengkapi isinya:
   ```bash
   cp .env.example .env
   ```
2. Jalankan server lokal:
   ```bash
   python main.py
   # atau
   uvicorn main:app --reload --port 8000
   ```
3. Buka browser di `http://localhost:8000/docs` untuk mencoba test endpoint `/manual-post` secara langsung.
