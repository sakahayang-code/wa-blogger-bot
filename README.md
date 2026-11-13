# 🤖 WhatsApp AI Blogger Bot (Termux Android)

Bot otomatis berbasis **Python** dan **Google Gemini Flash AI** yang berjalan langsung di ponsel **Android via Termux** (tanpa Node.js, tanpa Render, dan tanpa Fonnte). Bot ini secara otomatis menghasilkan artikel SEO lengkap, membuat gambar thumbnail 16:9, dan langsung menerbitkannya ke blog Blogger dengan template **Median UI**.

---

## 🌟 Keunggulan Versi Termux Android

* **🚫 Tanpa Node.js & Tanpa Render:** Berjalan 100% lokal di HP Android Anda menggunakan Python.
* **📱 Tanpa Gateway Pihak Ketiga (Bebas Fonnte):** Menggunakan aplikasi jembatan lokal Android (**AutoResponder for WA** / **MacroDroid**) yang terhubung ke `http://localhost:8000`.
* **🔒 100% Aman & Anti-Banned:** Tidak membajak socket WhatsApp, melainkan membaca & merespons pesan secara resmi via sistem notifikasi Android.
* **🎨 Khusus Template Median UI:** Artikel berformat tag HTML rapi, alert box info, FAQ item, dan thumbnail otomatis terpasang sebagai *Featured Image / Cover*.
* **⚡ 2 Mode Penggunaan:**
  1. **Mode WhatsApp:** Cukup kirim chat `!tulis <topik>` dari HP.
  2. **Mode Perintah Termux (CLI):** Ketik langsung `python post.py "topik artikel"` di Termux.

---

## 🛠️ Panduan Instalasi di Termux Android

### 1. Persiapan Termux
> ⚠️ **PENTING:** Unduh Termux dari [F-Droid](https://f-droid.org/en/packages/com.termux/) (versi Play Store sudah usang dan sering error saat install paket).

Buka aplikasi Termux di HP Android Anda, lalu ketik perintah berikut:
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### 2. Unduh Repositori Bot
```bash
git clone https://github.com/sakahayang-code/wa-blogger-bot.git
cd wa-blogger-bot
```

### 3. Pasang Dependensi Python
```bash
pip install -r requirements.txt
```

### 4. Atur Konfigurasi `.env`
Salin template konfigurasi:
```bash
cp .env.example .env
nano .env
```
Isi konfigurasi Anda:
* `GEMINI_API_KEY`: Dapatkan gratis di [Google AI Studio](https://aistudio.google.com/).
* `GEMINI_MODEL`: `gemini-2.5-flash`

#### Mengatur Akses ke Blogger (Pilih salah satu metode):
* **Metode A (Mail-to-Blogger - Paling Simpel):**
  * `BLOGGER_EMAIL`: Alamat email rahasia Blogger Anda (lihat solusi di bawah jika sebelumnya tidak bisa di-save).
  * `GMAIL_USER`: Email Gmail Anda.
  * `GMAIL_APP_PASSWORD`: Sandi aplikasi 16 karakter dari [Google App Passwords](https://myaccount.google.com/apppasswords).
* **Metode B (Google Blogger API v3 Resmi):**
  * `BLOGGER_BLOG_ID`: ID angka blog Anda (ada di URL dashboard Blogger).
  * Letakkan file `service_account.json` dari Google Cloud Console di dalam folder `wa-blogger-bot`.

*(Tekan `CTRL + X`, lalu tekan `Y`, lalu `Enter` untuk menyimpan di editor nano).*

---

## 📱 Cara Menghubungkan ke WhatsApp di Android (Tanpa Fonnte)

Agar bot merespons pesan WhatsApp Anda secara otomatis:

1. Di ponsel Android Anda, pasang aplikasi gratis **AutoResponder for WA** (dari Google Play Store).
2. Buka AutoResponder for WA dan beri izin akses notifikasi.
3. Buat Aturan Baru (klik tanda **+**):
   * **Pesan yang diterima:** Pilih *Pola kecocokan* atau *Berisi*, lalu masukkan: `!tulis *`
   * Scroll ke bawah ke bagian **Hubungkan Webserver (Connect Webserver / Webhook)**:
     * Aktifkan toggle Webhook.
     * **URL:** `http://localhost:8000/webhook?sync=true`
     * **Metode HTTP:** `POST`
     * **Header:** `Content-Type: application/json`
     * **Body (JSON):**
       ```json
       {"sender": "%sender%", "message": "%message%"}
       ```
4. Simpan aturan tersebut.
5. Jalankan server bot di Termux:
   ```bash
   python main.py
   ```
6. **Selesai!** Sekarang setiap kali ada pesan WhatsApp masuk diawali `!tulis <topik>`, Termux akan langsung meracik artikel SEO + thumbnail dan menerbitkannya ke blog Anda, lalu AutoResponder langsung mengirim balasan sukses ke chat WhatsApp!

---

## 💻 Cara Menggunakan Langsung dari Termux (Tanpa WhatsApp)

Jika Anda sedang membuka Termux dan ingin langsung memposting artikel tanpa lewat WhatsApp, cukup ketik:

```bash
python post.py "7 tips merawat laptop agar tidak cepat panas"
```

Bot akan langsung:
1. Menulis artikel lengkap dengan Google Gemini Flash.
2. Membuat gambar thumbnail 16:9.
3. Menerbitkannya ke Blogger (Median UI).
4. Menampilkan status sukses di layar terminal Termux.

---

## 💡 Solusi: "Blogger Email Tidak Bisa di Save"

Jika sebelumnya Anda mengalami tombol *Simpan* di menu **Publikasikan postingan menggunakan email** Blogger tidak berfungsi, ikuti aturan ketat dari Google ini:

1. **Kata Rahasia Hanya Huruf Kecil & Angka:**
   * ❌ *Salah:* `Artikel_Ku!`, `Post 2025`, `admin`
   * ✅ *Benar:* `post8899xyz`, `artikel77auto`, `botwa123`
2. **Pilihan Radio Button:**
   * Pastikan Anda mengklik radio button **Publikasikan email segera** (jangan biarkan di opsi *Dinonaktifkan*).
3. **Panjang Karakter:**
   * Minimal 4 sampai 8 karakter.
4. **Coba di Tab Incognito:**
   * Jika masih gagal, buka `blogger.com` di Chrome mode Incognito (seringkali ekstensi browser memblokir script popup Google).
