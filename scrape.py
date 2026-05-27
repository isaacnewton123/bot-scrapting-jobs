import html
import urllib.error
import os
import urllib.request
import json
import re
from html.parser import HTMLParser
import boto3
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"\'')


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_html(target_url):
    req = urllib.request.Request(target_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.in_content = False
        self.title = ""
        self.content = []
        self.apply_page_url = None
        self.current_content = ""
        self.div_depth = 0
        self.content_div_depth = -1
        self.in_a = False
        self.current_href = ""
        self.published_time = ""
        self.og_image = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "meta":
            if attrs_dict.get("property") == "article:published_time":
                self.published_time = attrs_dict.get("content", "")
            if attrs_dict.get("property") == "og:image":
                self.og_image = attrs_dict.get("content", "")
                
        if tag == "h1" and "entry-title" in attrs_dict.get("class", ""):
            self.in_title = True
        
        if tag == "div":
            self.div_depth += 1
            if "entry-content" in attrs_dict.get("class", ""):
                self.in_content = True
                self.content_div_depth = self.div_depth

        if tag == "a" and self.in_content:
            self.in_a = True
            self.current_href = attrs_dict.get("href", "")
            if self.current_href.endswith("/apply/"):
                self.apply_page_url = self.current_href

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_title = False
        if tag == "div":
            if self.div_depth == self.content_div_depth:
                self.in_content = False
                self.content_div_depth = -1
            self.div_depth -= 1
        
        if tag == "a":
            self.in_a = False
            self.current_href = ""

        if tag in ["p", "li", "h2", "h3", "h4", "td"] and self.in_content:
            if self.current_content.strip():
                self.content.append(self.current_content.strip())
            self.current_content = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        if self.in_content:
            self.current_content += data

class ApplyPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.apply_links = []
        self.in_ul = False
        self.in_li = False
        self.in_a = False
        self.ul_class = ""
        self.current_href = ""
        self.current_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "ul":
            self.in_ul = True
            self.ul_class = attrs_dict.get("class", "")
        if tag == "li" and self.in_ul and "pjs-download-list" in self.ul_class:
            self.in_li = True
        if tag == "a" and self.in_li:
            self.in_a = True
            self.current_href = attrs_dict.get("href", "")

    def handle_endtag(self, tag):
        if tag == "ul":
            self.in_ul = False
        if tag == "li":
            self.in_li = False
        if tag == "a" and self.in_a:
            self.in_a = False
            if self.current_href:
                self.apply_links.append({
                    "url": self.current_href,
                    "method": self.current_text.strip()
                })
            self.current_href = ""
            self.current_text = ""

    def handle_data(self, data):
        if self.in_a:
            self.current_text += data

def clean_and_structure_content(raw_content):
    jobs = []
    current_job = None
    description = []
    metadata = {}
    
    i = 0
    while i < len(raw_content):
        text = raw_content[i].strip()
        
        # Meta extraction
        if text == "Lokasi:" and i + 1 < len(raw_content):
            metadata["location"] = raw_content[i+1].strip()
            i += 2
            continue
        if text == "Jenis Pekerjaan:" and i + 1 < len(raw_content):
            metadata["job_type"] = raw_content[i+1].strip()
            i += 2
            continue
        if text == "Pendidikan:" and i + 1 < len(raw_content):
            metadata["education"] = raw_content[i+1].strip()
            i += 2
            continue
        if text == "Tanggal publikasi:" and i + 1 < len(raw_content):
            i += 2
            continue
            
        # Ignore ads and junk
        junk_keywords = ["adsbygoogle", "Post Views:", "Perhatian :", "NOTE :", "Join Whatsapp", "Jika link error", "Posting terkait:"]
        if any(junk in text for junk in junk_keywords):
            i += 1
            continue
            
        pos_match = re.match(r'^(?:Posisi\s*:\s*|\d+[\.\)]+\s+)(.+)$', text, re.IGNORECASE)
        if pos_match and len(text) < 100:
            if current_job:
                jobs.append(current_job)
            current_job = {"position": pos_match.group(1).strip(), "requirements": []}
            i += 1
            continue
            
        if current_job:
            if text.strip().lower() in ["kualifikasi :", "kualifikasi:", "persyaratan:", "persyaratan :"]:
                i += 1
                continue
            
            # End of job listing
            if text.lower().startswith("apabila semua syarat") or text.lower().startswith("silakan mendaftar") or text.lower().startswith("apply here") or text.lower().startswith("pt pgas solution"):
                jobs.append(current_job)
                current_job = None
                i += 1
                continue
                
            current_job["requirements"].append(text.strip())
        else:
            description.append(text.strip())
        
        i += 1
            
    if current_job:
        jobs.append(current_job)
        
    return description, jobs, metadata

def rewrite_with_ai(text, company, jobs):
    api_key = os.environ.get("GEMINI_API_KEY")
    fallback = {
        "slug": company.lower().replace(' ', '-').replace('.', ''),
        "category": "Lainnya",
        "meta_title": f"Lowongan Kerja {company}",
        "meta_description": f"Daftar lowongan kerja terbaru di {company}.",
        "tags": ["Lowongan Kerja"],
        "section_1": {"header": "", "paragraphs": [p.strip() for p in text.split('\n') if p.strip()]},
        "section_2": {"header": "", "paragraphs": []},
        "salaries": [],
        "section_3": {"header": "", "paragraphs": []},
        "section_4": {"header": "", "paragraphs": []},
        "section_5": {"header": "", "paragraphs": []}
    }
    if not api_key:
        return fallback
    
    positions = ", ".join([job["position"] for job in jobs]) if jobs else "Lowongan Kerja"

    prompt = (
        "Tulis ulang deskripsi lowongan pekerjaan ini agar unik, tidak terlihat duplikat, dan SANGAT OPTIMAL UNTUK SEO. "
        "Gunakan bahasa Indonesia yang profesional dan informatif.\n\n"
        "ATURAN PENTING:\n"
        f"1. Sisipkan kata kunci (keyword) berikut secara natural: 'Lowongan kerja', 'Loker', 'Karir', '{company}', '{positions}'.\n"
        "2. Buatlah ke dalam 5 Section (section_1 sampai section_5) tanpa ada Markdown Markdown Markdown sedikit pun. Semua isi teks harus murni text JSON yang valid. Jangan gunakan raw markdown (seperti ```json).\n"
        "3. Tulis setiap section secara panjang, mendetail, dan sangat informatif (minimal 2 paragraf per section) menggunakan gaya bahasa storytelling atau copywriting yang profesional untuk memaksimalkan kata kunci SEO.\n"
        "4. Jangan gunakan format list (1,2,3) atau bullet points di dalam paragraf. Tulis murni dalam bentuk prosa/artikel naratif.\n"
        "5. Section 1 dan 2 ditempatkan SEBELUM tabel Gaji. Pastikan akhir paragraf Section 2 mengarahkan pembaca untuk melihat tabel gaji. Section 3 dan 4 ditempatkan SETELAH tabel Gaji dan SEBELUM daftar Posisi & Kualifikasi. Pastikan akhir paragraf Section 4 mengarahkan pembaca untuk melihat posisi pekerjaan dan kualifikasi yang ada di bawahnya.\n"
        "6. Section 5 adalah penutup dan ajakan (Call to Action) sebelum link pendaftaran.\n"
        "7. Ekstrak informasi gaji dari teks asli ke dalam array 'salaries'. Jika tidak ada info gaji, biarkan array kosong [].\n"
        "8. Buatkan 'slug' URL super SEO-friendly, 'meta_title' memancing klik (maks 60 karakter), dan 'meta_description' (maks 150 karakter). Untuk array 'tags', BERIKAN MINIMAL 10-15 TAGS populer dan sangat relevan (termasuk sinonim jabatan, nama daerah, jenis industri, tipe pekerjaan, misal: 'Loker Cikarang', 'Pabrik', 'SMA/SMK', dll) untuk menyapu bersih semua trafik pencarian.\n"
        "9. Tentukan SATU 'category' utama untuk perusahaan/pekerjaan ini (misalnya: 'Manufaktur & Pabrik', 'F&B dan Restoran', 'IT & Teknologi', 'Logistik & Gudang', 'Retail', 'Kesehatan', 'Administrasi', atau buat sendiri yang relevan).\n"
        "10. Anda HARUS merespon dengan format JSON murni seperti ini:\n"
        "{\n"
        '  "slug": "lowongan-kerja-pt-oneject-indonesia-jawa-barat",\n'
        '  "category": "Manufaktur & Pabrik",\n'
        '  "meta_title": "Lowongan Kerja PT Oneject Indonesia Terbaru",\n'
        '  "meta_description": "...",\n'
        '  "tags": ["Manufaktur", "Alat Kesehatan"],\n'
        '  "section_1": {"header": "Judul 1", "paragraphs": ["Paragraf 1"]}, \n'
        '  "section_2": {"header": "Judul 2", "paragraphs": ["Paragraf yg mengarahkan ke tabel gaji"]}, \n'
        '  "salaries": [{"position": "nama posisi", "salary": "nominal/rentang gaji"}],\n'
        '  "section_3": {"header": "Judul 3", "paragraphs": ["Paragraf lanjutan"]}, \n'
        '  "section_4": {"header": "Judul 4", "paragraphs": ["Paragraf lanjutan"]}, \n'
        '  "section_5": {"header": "Judul 5", "paragraphs": ["Paragraf penutup"]}\n'
        "}\n"
        "11. Gunakan teknik LSI (Latent Semantic Indexing) secara natural di seluruh paragraf. Rata kanan SEO-nya! Sikat habis semua keyword pencarian potensial tanpa terlihat seperti spam.\n\n"
        f"Deskripsi Asli:\n{text}"
    )
    
    models = [
        "gemini-3.5-flash",
        "gemini-3-flash",
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite"
    ]

    headers = {'Content-Type': 'application/json'}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }).encode('utf-8')

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            print(f"Mencoba AI model: {model}...")
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                raw_ai = result['candidates'][0]['content']['parts'][0]['text']
                
                # Try parsing to make sure it's valid JSON
                ai_json = json.loads(raw_ai)
                print(f"Berhasil menggunakan model: {model}!")
                return ai_json
        except Exception as e:
            print(f"Gagal menggunakan {model}: {e}. Beralih ke model selanjutnya...")
            continue
            
    print("Semua model AI gagal/sibuk. Menggunakan teks fallback mentah.")
    return fallback

def upload_image_to_r2(image_url, slug):
    r2_account_id = os.environ.get("R2_ACCOUNT_ID")
    r2_access_key = os.environ.get("R2_ACCESS_KEY_ID")
    r2_secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    r2_bucket = os.environ.get("R2_BUCKET_NAME")
    r2_domain = os.environ.get("R2_PUBLIC_DOMAIN")
    
    if not all([r2_account_id, r2_access_key, r2_secret_key, r2_bucket, r2_domain]):
        print("R2 credentials not complete, skipping upload.")
        return None

    try:
        req = urllib.request.Request(image_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            image_data = response.read()
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            ext = ".jpg"
            if "png" in content_type: ext = ".png"
            elif "webp" in content_type: ext = ".webp"
            
            filename = f"{slug}{ext}"
            
            s3 = boto3.client(
                's3',
                endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=r2_access_key,
                aws_secret_access_key=r2_secret_key
            )
            
            s3.put_object(
                Bucket=r2_bucket,
                Key=filename,
                Body=image_data,
                ContentType=content_type
            )
            
            public_url = r2_domain
            if not public_url.startswith("http"):
                public_url = "https://" + public_url
            if not public_url.endswith("/"):
                public_url += "/"
            
            return f"{public_url}{filename}"
            
    except Exception as e:
        print(f"Error uploading image to R2: {e}")
        return None

def save_to_mongodb(data):
    mongo_uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "nyarikerja_db")
    collection_name = os.environ.get("MONGODB_COLLECTION_NAME", "jobs")
    
    if not mongo_uri:
        print("ERROR: MONGODB_URI belum diset di .env")
        return False
        
    try:
        # Menambahkan data kapan loker ini dimasukkan/diperbarui
        data['updated_at'] = datetime.utcnow().isoformat() + "Z"
        if 'created_at' not in data:
            data['created_at'] = data['updated_at']
            
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        db = client[db_name]
        collection = db[collection_name]
        
        # Upsert berdasarkan original_url
        original_url = data.get("original_url")
        if not original_url:
            print("ERROR: original_url tidak ditemukan dalam data.")
            return False
            
        result = collection.update_one(
            {"original_url": original_url},
            {"$set": data},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"Sukses! Loker BARU dimasukkan ke MongoDB dengan ID: {result.upserted_id}")
        else:
            print(f"Sukses! Loker LAMA ({original_url}) di-Update di MongoDB.")
            
        client.close()
        return True
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return False

def process_job_url(target_url):
    html = fetch_html(target_url)
    parser = MyHTMLParser()
    parser.feed(html)

    if parser.current_content.strip():
        parser.content.append(parser.current_content.strip())

    desc, jobs, metadata = clean_and_structure_content(parser.content)
    title_clean = parser.title.replace(" - Bukajobs Media", "").strip()

    original_desc_text = "\n".join(desc)
    ai_result = rewrite_with_ai(original_desc_text, title_clean, jobs)

    slug = ai_result.get("slug", title_clean.lower().replace(' ', '-').replace('.', ''))
    
    image_url = ""
    if parser.og_image:
        print(f"Ditemukan gambar: {parser.og_image}, mengunggah ke R2...")
        r2_url = upload_image_to_r2(parser.og_image, slug)
        if r2_url:
            image_url = r2_url
            print(f"Gambar berhasil diunggah ke R2: {r2_url}")

    result = {
        "original_url": target_url,
        "company": title_clean,
        "slug": slug,
        "image_url": image_url,
        "location": metadata.get("location", ""),
        "job_type": metadata.get("job_type", ""),
        "education": metadata.get("education", ""),
        "seo": {
            "meta_title": ai_result.get("meta_title", ""),
            "meta_description": ai_result.get("meta_description", ""),
            "tags": ai_result.get("tags", [])
        },
        "category": ai_result.get("category", "Lainnya"),
        "section_1": ai_result.get("section_1", {"header": "", "paragraphs": []}),
        "section_2": ai_result.get("section_2", {"header": "", "paragraphs": []}),
        "salaries": ai_result.get("salaries", []),
        "section_3": ai_result.get("section_3", {"header": "", "paragraphs": []}),
        "section_4": ai_result.get("section_4", {"header": "", "paragraphs": []}),
        "jobs": jobs,
        "section_5": ai_result.get("section_5", {"header": "", "paragraphs": []}),
        "apply_links": []
    }

    if parser.apply_page_url:
        try:
            apply_html = fetch_html(parser.apply_page_url)
            apply_parser = ApplyPageParser()
            apply_parser.feed(apply_html)
            result["apply_links"] = apply_parser.apply_links
        except Exception as e:
            result["apply_error"] = str(e)

    # Find email addresses in the content
    emails = []
    for text in parser.content:
        matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        emails.extend(matches)

    emails = list(set(emails))
    for email in emails:
        result["apply_links"].append({
            "url": f"mailto:{email}",
            "method": "Apply via Email"
        })
        
    return result

if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://bukajobs.com/pt-oneject-indonesia/"
    print(f"Scraping {test_url}...")
    result_data = process_job_url(test_url)
    
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=4, ensure_ascii=False)
    
    print("Berhasil mengekstrak data dan menyimpannya ke dalam file result.json")
