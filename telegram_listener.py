import os
import re
import json
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from scrape import process_job_url, save_to_mongodb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"\'')

api_id = os.environ.get('TELEGRAM_API_ID')
api_hash = os.environ.get('TELEGRAM_API_HASH')
channel_username = os.environ.get('TELEGRAM_CHANNEL', 'bukajobs') # Bisa berupa ID channel atau username
string_session_env = os.environ.get('TELEGRAM_STRING_SESSION', '')

if not api_id or not api_hash:
    print("=======================================================================")
    print("ERROR: TELEGRAM_API_ID dan TELEGRAM_API_HASH belum diset di file .env")
    print("Silakan dapatkan dari https://my.telegram.org lalu tambahkan ke .env")
    print("=======================================================================")
    exit(1)

# Jika StringSession kosong, Telethon akan meminta nomor HP dan OTP.
client = TelegramClient(StringSession(string_session_env), api_id, api_hash)

@client.on(events.NewMessage(chats=channel_username))
async def my_event_handler(event):
    message_text = event.raw_text
    logger.info(f"Pesan baru terdeteksi dari channel {channel_username}!")
    
    # Cari URL bukajobs.com
    match = re.search(r'(https://bukajobs\.com/[^\s]+)', message_text)
    if match:
        url = match.group(1).strip()
        logger.info(f"Ditemukan URL Bukajobs: {url}")
        
        try:
            # Panggil fungsi scraper dan AI yang sudah kita buat
            logger.info("Memulai proses ekstraksi dan AI rewriting...")
            result = process_job_url(url)
            
            # Simpan hasil langsung ke MongoDB
            logger.info("Menyimpan data ke MongoDB Atlas...")
            success = save_to_mongodb(result)
            
            if success:
                logger.info(f"BERHASIL! Data disimpan ke MongoDB.")
            else:
                logger.error("GAGAL menyimpan data ke MongoDB!")
            
        except Exception as e:
            logger.error(f"Terjadi kesalahan saat memproses URL: {e}")
    else:
        logger.info("Tidak ada URL Bukajobs yang ditemukan di dalam pesan ini. Mengabaikan...")

async def main():
    await client.start() # type: ignore
    
    # Save the string session back to .env if it was just generated
    if not string_session_env:
        new_session_string = client.session.save()
        logger.info("MENDAPATKAN STRING SESSION BARU! Menyimpan otomatis ke .env...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("TELEGRAM_STRING_SESSION="):
                    f.write(f"TELEGRAM_STRING_SESSION={new_session_string}\n")
                else:
                    f.write(line)
        logger.info("String Session berhasil disimpan ke .env. Anda siap untuk deploy ke Koyeb!")

    print(f"Menjalankan Telegram Listener untuk channel: {channel_username}...")
    print("Tekan Ctrl+C untuk berhenti.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
