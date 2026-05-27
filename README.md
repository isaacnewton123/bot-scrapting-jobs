# NyariKerja Auto Scraper Bot 🤖💼

Bot Python otomatis (Serverless/Worker) yang bertugas mendengarkan pesan dari Telegram secara *real-time*, mengekstrak tautan lowongan kerja dari berbagai sumber website portal karir, menulis ulang (*rewrite*) kontennya menggunakan AI (Gemini Flash) agar 100% unik & ramah SEO, dan menyimpannya langsung ke database MongoDB Atlas.

Bot ini dirancang khusus untuk berjalan secara mandiri 24/7 di layanan cloud gratis selamanya seperti Render.com.

## Fitur Utama ✨
1. **Telegram Listener:** Bereaksi instan saat ada pesan masuk di Channel Telegram yang ditentukan.
2. **AI Rewriter (Google Gemini):** Menyulap deskripsi pekerjaan asli menjadi format yang lebih rapi, terstruktur, dan dioptimalkan dengan *slug*, *meta title*, *meta description*, dan *tags* untuk SEO (Rata Kanan).
3. **Cloudflare R2 Storage:** Otomatis mengunduh gambar loker dari web asal dan mengunggahnya ke CDN Cloudflare R2 yang super cepat.
4. **Smart MongoDB Upsert:** Menyimpan hasil akhir JSON ke MongoDB Atlas. Jika loker sudah pernah ada (berdasarkan `original_url`), bot hanya akan memperbarui data (*Update*) agar konten tidak ganda (Anti Duplicate Content).
5. **String Session:** Menggunakan `Telethon StringSession` sehingga kebal dari proses *restart* server (cocok untuk hosting gratisan yang sering *sleep/restart*).

## Deployment (Cara Pasang di Render.com) 🚀

Render adalah pilihan tepat karena menyediakan *Web Service* gratis selamanya. Karena Render akan "menidurkan" server jika tidak ada kunjungan dalam 15 menit, bot ini sudah dilengkapi dengan **Web Server Mini Otomatis**. Anda hanya perlu menggunakan layanan *Ping* gratis seperti cron-job.org untuk menjaganya tetap hidup.

### 1. Persiapkan Environment Variables (Secrets)
Siapkan kredensial berikut dan masukkan ke bagian **Environment Variables** di Dashboard Render:

```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_CHANNEL=username_channel_telegram
TELEGRAM_STRING_SESSION=your_long_string_session

R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=your_bucket_name
R2_PUBLIC_DOMAIN=https://cdn.domainanda.com

MONGODB_URI=mongodb+srv://username:password@cluster...
MONGODB_DB_NAME=nyarikerja_db
MONGODB_COLLECTION_NAME=jobs
```

### 2. Set Konfigurasi di Render
Saat membuat **New Web Service** di Render:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python telegram_listener.py`

Klik **Deploy**. Render akan memberi Anda sebuah URL gratis (misalnya `https://bot-scraper.onrender.com`).

### 3. Jaga Bot Tetap Hidup (Anti-Sleep)
Buka [cron-job.org](https://cron-job.org/) (Gratis):
1. Buat akun dan klik **Create Cronjob**.
2. Masukkan URL Render Anda tadi (tambahkan `/ping` di belakangnya, contoh: `https://bot-scraper.onrender.com/ping`).
3. Set jadwalnya agar mengunjungi URL tersebut setiap **14 menit**.
4. Selesai! Bot Anda akan hidup abadi tanpa henti.

---
*Dibangun untuk nyarikerja.online - Mengubah kerja keras menjadi kerja cerdas.*
