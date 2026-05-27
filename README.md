# NyariKerja Auto Scraper Bot 🤖💼

Bot Python otomatis (Serverless/Worker) yang bertugas mendengarkan pesan dari Telegram secara *real-time*, mengekstrak tautan lowongan kerja dari berbagai sumber website portal karir, menulis ulang (*rewrite*) kontennya menggunakan AI (Gemini Flash) agar 100% unik & ramah SEO, dan menyimpannya langsung ke database MongoDB Atlas.

Bot ini dirancang khusus untuk berjalan secara mandiri 24/7 di layanan cloud (seperti Koyeb).

## Fitur Utama ✨
1. **Telegram Listener:** Bereaksi instan saat ada pesan masuk di Channel Telegram yang ditentukan.
2. **AI Rewriter (Google Gemini):** Menyulap deskripsi pekerjaan asli menjadi format yang lebih rapi, terstruktur, dan dioptimalkan dengan *slug*, *meta title*, *meta description*, dan *tags* untuk SEO (Rata Kanan).
3. **Cloudflare R2 Storage:** Otomatis mengunduh gambar loker dari web asal dan mengunggahnya ke CDN Cloudflare R2 yang super cepat.
4. **Smart MongoDB Upsert:** Menyimpan hasil akhir JSON ke MongoDB Atlas. Jika loker sudah pernah ada (berdasarkan `original_url`), bot hanya akan memperbarui data (*Update*) agar konten tidak ganda (Anti Duplicate Content).
5. **String Session:** Menggunakan `Telethon StringSession` sehingga kebal dari proses *restart* server (cocok untuk hosting gratisan yang sering *sleep/restart*).

## Deployment (Cara Pasang di Koyeb) 🚀

Koyeb adalah pilihan sempurna untuk bot ini karena menyediakan *Free Worker* yang berjalan 24 jam penuh tanpa perlu dipancing *traffic* (berbeda dengan Render).

### 1. Persiapkan Environment Variables (Secrets)
Siapkan kredensial berikut dan masukkan ke bagian **Environment Variables** di Dashboard Koyeb:

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

### 2. Set Run Command di Koyeb
Pada tahap *Deployment*, Anda hanya perlu menetapkan satu perintah:
- **Build Command:** *(Kosongkan)*
- **Run Command:** `python telegram_listener.py`

Klik Deploy, dan dalam 2-3 menit, bot Anda akan hidup di awan mencari lowongan kerja untuk Anda!

---
*Dibangun untuk nyarikerja.online - Mengubah kerja keras menjadi kerja cerdas.*
