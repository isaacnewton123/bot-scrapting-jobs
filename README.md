# 🤖 NyariKerja Bot

Bot otomatis untuk scraping, rewriting, dan penyimpanan data lowongan kerja dari channel Telegram ke MongoDB Atlas.

## ✨ Fitur Utama

- **Telegram Listener** — Mendengarkan pesan baru di channel Telegram secara real-time
- **Auto Scraper** — Mengekstrak data lowongan dari URL yang ditemukan (judul, konten, gambar, link apply)
- **AI Rewriting (Gemini)** — Menulis ulang deskripsi agar unik dan SEO-optimized menggunakan Gemini API
- **Image Upload (Cloudflare R2)** — Mengunduh dan mengunggah gambar lowongan ke CDN
- **MongoDB Atlas** — Menyimpan data terstruktur dengan sistem upsert (tidak duplikat)
- **Status Dashboard** — Halaman web informatif untuk monitoring bot secara real-time
- **Type-Safe** — Seluruh kode menggunakan TypedDict (tanpa `Any`) untuk keamanan tipe data

## 📁 Struktur Folder

```
bot/
├── models.py              # Type definitions (TypedDict) — 8 tipe data
├── config.py              # Load .env, validasi, export config bertipe
├── logger.py              # Console-only logging (stdout untuk Render)
├── parsers.py             # HTML parser + content cleaner
├── ai_rewriter.py         # Prompt template + Gemini API call
├── storage.py             # Upload R2 + simpan MongoDB
├── stats.py               # In-memory stats tracker
├── status_page.py         # HTML status page builder
├── scrape.py              # Pipeline utama (scrape → AI → upload → save)
├── telegram_listener.py   # Telegram channel listener (entry point)
├── requirements.txt       # Dependencies
└── .env                   # Environment variables (JANGAN commit!)
```

## 🔧 Konfigurasi

Buat file `.env` di dalam folder `bot/` dengan isi berikut:

```env
# Telegram (wajib)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_CHANNEL=nama_channel
TELEGRAM_STRING_SESSION=

# Gemini AI (wajib)
GEMINI_API_KEY=your_gemini_api_key

# Cloudflare R2 (opsional, untuk upload gambar)
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket
R2_PUBLIC_DOMAIN=https://your-domain.r2.dev

# MongoDB Atlas (wajib)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=nyarikerja_db
MONGODB_COLLECTION_NAME=jobs
```

### Cara Mendapatkan Credentials

| Credential | Sumber |
|---|---|
| `TELEGRAM_API_ID` & `TELEGRAM_API_HASH` | [my.telegram.org](https://my.telegram.org) |
| `TELEGRAM_STRING_SESSION` | Otomatis di-generate saat pertama kali login |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `R2_*` | [Cloudflare Dashboard → R2](https://dash.cloudflare.com) |
| `MONGODB_URI` | [MongoDB Atlas](https://cloud.mongodb.com) |

## 🚀 Menjalankan Lokal

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Jalankan listener (akan meminta nomor HP untuk login Telegram pertama kali)
python telegram_listener.py

# 3. Atau jalankan scraper manual (tanpa Telegram)
python scrape.py https://example.com/lowongan/
```

## 🌐 Deploy ke Render

### Pengaturan Render Web Service

| Setting | Value |
|---|---|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python telegram_listener.py` |
| **Environment** | `Python 3` |
| **Plan** | Free |

### Environment Variables di Render

Tambahkan semua variabel dari `.env` ke **Render Dashboard → Environment**.

> ⚠️ **Penting:** `TELEGRAM_STRING_SESSION` harus diisi terlebih dahulu. Jalankan bot di lokal sekali untuk men-generate session, lalu salin nilainya ke Render.

### Health Check

Render akan otomatis melakukan ping ke `/ping` untuk memastikan bot tetap hidup. Bot menyediakan:
- `GET /` — Halaman status HTML dengan statistik real-time
- `GET /ping` — Response `ok` untuk health check

## 📊 Status Dashboard

Saat bot berjalan, buka URL Render Anda di browser untuk melihat dashboard:

- 🟢 Status bot (hidup/mati)
- ⏱️ Uptime
- 📈 Total berhasil / gagal / URL ditemukan
- 📊 Success rate
- 🏢 Perusahaan terakhir diproses

> Dashboard ini **tidak menampilkan data sensitif** (API key, URI database, session).

## 🔄 Alur Kerja Bot

```
Channel Telegram → Pesan Baru Terdeteksi
       ↓
   Cari URL lowongan di dalam pesan
       ↓
   Fetch HTML & Parse konten
       ↓
   Bersihkan dari iklan, disclaimer, social links
       ↓
   Kirim ke Gemini AI untuk rewriting + SEO
       ↓
   Upload gambar ke Cloudflare R2
       ↓
   Simpan ke MongoDB Atlas (upsert)
       ↓
   ✅ Selesai — data siap tampil di frontend
```

## 🛡️ Keamanan

- File `.env` masuk `.gitignore` — tidak pernah ter-commit
- Status page tidak menampilkan credential
- `TELEGRAM_STRING_SESSION` bersifat rahasia — jangan bagikan ke siapapun
- MongoDB menggunakan connection string `+srv` dengan TLS

## 📝 Lisensi

© 2026 NyariKerja.online — All rights reserved.
