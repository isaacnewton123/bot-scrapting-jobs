"""
status_page.py — HTML status page builder.

Satu modul, satu tanggung jawab: generate HTML halaman status.
Tidak ada logika bisnis, hanya presentasi.
"""

from __future__ import annotations

from stats import get_stats, get_success_rate, get_uptime


def build_status_html() -> str:
    """Generate HTML status page — tanpa data sensitif apapun."""
    stats = get_stats()
    uptime = get_uptime()
    success_rate = get_success_rate()
    status_emoji = "🟢" if stats["started_at"] else "🔴"

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot NyariKerja — Status</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0A0E1A;
            color: #F1F5F9;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 40px;
            max-width: 480px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .header .status {{
            font-size: 0.9rem;
            color: #94A3B8;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }}
        .stat .value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #6C63FF;
        }}
        .stat .label {{
            font-size: 0.75rem;
            color: #94A3B8;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.875rem;
        }}
        .info-row:last-child {{ border-bottom: none; }}
        .info-row .key {{ color: #94A3B8; }}
        .info-row .val {{
            color: #F1F5F9;
            font-weight: 600;
            text-align: right;
            max-width: 55%;
            word-break: break-all;
        }}
        .footer {{
            text-align: center;
            margin-top: 24px;
            font-size: 0.75rem;
            color: #475569;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>{status_emoji} Bot NyariKerja</h1>
            <div class="status">Telegram Listener &bull; Uptime: {uptime}</div>
        </div>
        <div class="grid">
            <div class="stat">
                <div class="value">{stats['total_success']}</div>
                <div class="label">Berhasil</div>
            </div>
            <div class="stat">
                <div class="value">{stats['total_errors']}</div>
                <div class="label">Gagal</div>
            </div>
            <div class="stat">
                <div class="value">{stats['total_urls_found']}</div>
                <div class="label">URL Ditemukan</div>
            </div>
            <div class="stat">
                <div class="value">{success_rate}</div>
                <div class="label">Success Rate</div>
            </div>
        </div>
        <div class="info-row">
            <span class="key">Channel</span>
            <span class="val">{stats['channel_name']}</span>
        </div>
        <div class="info-row">
            <span class="key">Total Pesan Masuk</span>
            <span class="val">{stats['total_messages']}</span>
        </div>
        <div class="info-row">
            <span class="key">Perusahaan Terakhir</span>
            <span class="val">{stats['last_company']}</span>
        </div>
        <div class="info-row">
            <span class="key">Waktu Terakhir</span>
            <span class="val">{stats['last_processed_at']}</span>
        </div>
        <div class="footer">
            NyariKerja.online &copy; 2026
        </div>
    </div>
</body>
</html>"""
