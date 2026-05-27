"""
scrape.py — Pipeline utama untuk scraping dan processing lowongan kerja.

Alur:
1. Fetch HTML dari BukaJobs
2. Parse konten dengan MyHTMLParser
3. Bersihkan teks dengan clean_and_structure_content
4. Rewrite dengan AI (Gemini)
5. Upload gambar ke R2
6. Ekstrak link pendaftaran + email
7. Return data terstruktur siap MongoDB

Usage:
    python scrape.py                              # Default: PT Oneject
    python scrape.py https://bukajobs.com/xxx/    # URL spesifik
"""

from __future__ import annotations

import json
import sys

from ai_rewriter import rewrite_with_ai
from logger import get_logger
from parsers import (
    ApplyPageParser,
    MyHTMLParser,
    clean_and_structure_content,
    extract_emails,
    fetch_html,
)
from storage import save_to_mongodb, upload_image_to_r2
from models import AIResult, ApplyLink, JobData

logger = get_logger(__name__)


def process_job_url(target_url: str) -> JobData:
    """Pipeline lengkap: scrape → clean → AI rewrite → upload gambar.
    
    Args:
        target_url: URL halaman lowongan di BukaJobs.
        
    Returns:
        JobData berisi data lowongan terstruktur siap disimpan ke MongoDB.
    """
    logger.info(f"{'='*60}")
    logger.info(f"MEMULAI PROSES: {target_url}")
    logger.info(f"{'='*60}")

    # 1. Fetch & Parse HTML
    logger.info("[1/6] Fetching dan parsing HTML...")
    html = fetch_html(target_url)
    parser = MyHTMLParser()
    parser.feed(html)
    parser.finalize()
    logger.info(f"Judul ditemukan: '{parser.title}'")
    logger.info(f"Konten mentah: {len(parser.content)} baris")

    # 2. Bersihkan konten
    logger.info("[2/6] Membersihkan konten dari sampah...")
    desc: list[str] = clean_and_structure_content(parser.content)
    title_clean: str = parser.title.replace(" - Bukajobs Media", "").strip()

    # 3. AI Rewriting
    logger.info("[3/6] Mengirim ke AI untuk rewriting...")
    original_desc_text: str = "\n".join(desc)
    ai_result: AIResult = rewrite_with_ai(original_desc_text, title_clean)

    # 4. Upload gambar ke R2
    slug: str = ai_result.get("slug", title_clean.lower().replace(" ", "-").replace(".", ""))
    image_url: str = ""
    if parser.og_image:
        logger.info(f"[4/6] Mengupload gambar: {parser.og_image}")
        r2_url = upload_image_to_r2(parser.og_image, slug)
        if r2_url:
            image_url = r2_url
    else:
        logger.info("[4/6] Tidak ada gambar OG ditemukan. Dilewati.")

    # 5. Susun hasil akhir
    logger.info("[5/6] Menyusun data akhir...")
    empty_section = {"header": "", "paragraphs": []}

    result: JobData = {
        "original_url": target_url,
        "company": title_clean,
        "slug": slug,
        "image_url": image_url,
        "location": ai_result.get("location", ""),
        "job_type": ai_result.get("job_type", ""),
        "education": ai_result.get("education", ""),
        "seo": {
            "meta_title": ai_result.get("meta_title", ""),
            "meta_description": ai_result.get("meta_description", ""),
            "tags": ai_result.get("tags", []),
        },
        "category": ai_result.get("category", "Lainnya"),
        "section_1": ai_result.get("section_1", empty_section),
        "section_2": ai_result.get("section_2", empty_section),
        "salaries": ai_result.get("salaries", []),
        "section_3": ai_result.get("section_3", empty_section),
        "section_4": ai_result.get("section_4", empty_section),
        "jobs": ai_result.get("jobs", []),
        "section_5": ai_result.get("section_5", empty_section),
        "apply_links": [],
    }

    # 6. Ekstrak link pendaftaran
    logger.info("[6/6] Mengekstrak link pendaftaran dan email...")
    apply_links: list[ApplyLink] = []

    if parser.apply_page_url:
        try:
            logger.info(f"Fetching halaman apply: {parser.apply_page_url}")
            apply_html = fetch_html(parser.apply_page_url)
            apply_parser = ApplyPageParser()
            apply_parser.feed(apply_html)
            apply_links.extend(apply_parser.apply_links)
            logger.info(f"Ditemukan {len(apply_parser.apply_links)} link pendaftaran.")
        except Exception as e:
            logger.warning(f"Gagal fetch halaman apply: {e}")
            result["apply_error"] = str(e)
    else:
        logger.info("Tidak ada halaman /apply/ ditemukan.")

    # Ekstrak email dari konten
    emails: list[str] = extract_emails(parser.content)
    for email in emails:
        apply_links.append(ApplyLink(url=f"mailto:{email}", method="Apply via Email"))

    result["apply_links"] = apply_links

    logger.info(f"PROSES SELESAI: {title_clean}")
    logger.info(f"  Posisi: {len(result.get('jobs', []))} | Apply links: {len(result['apply_links'])}")
    logger.info(f"{'='*60}")
    return result


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_url: str = sys.argv[1] if len(sys.argv) > 1 else "https://bukajobs.com/pt-oneject-indonesia/"
    logger.info(f"CLI Mode: Scraping {test_url}")

    result_data: JobData = process_job_url(test_url)

    output_file: str = "result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=4, ensure_ascii=False)

    logger.info(f"Hasil disimpan ke: {output_file}")
    print(f"\n✅ Berhasil! Data tersimpan di {output_file}")
