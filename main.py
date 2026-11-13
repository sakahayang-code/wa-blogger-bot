import logging
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from config import config
from services.gemini_service import gemini_service
from services.blogger_service import blogger_service
from services.whatsapp_service import whatsapp_service

# Atur logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("wa-blogger-bot")

app = FastAPI(
    title="WhatsApp AI Blogger Auto-Post Bot",
    description="Bot WhatsApp otomatis untuk menulis artikel SEO & thumbnail AI ke template Median UI Blogger.",
    version="1.0.0"
)

def process_and_publish_article(sender: str, topic: str):
    """
    Fungsi latar belakang (Background Task):
    1. Membuat konten artikel via Google Gemini.
    2. Membuat gambar thumbnail via Imagen 3 / fallback.
    3. Menerbitkan postingan ke Blogger via Mail-to-Blogger.
    4. Mengirim konfirmasi sukses ke WhatsApp pengirim.
    """
    try:
        logger.info(f"Mulai memproses topik: '{topic}' untuk pengirim: {sender}")
        
        # 1. Generate Artikel dengan Gemini
        article_data = gemini_service.generate_article(topic)
        title = article_data.get("title", f"Artikel: {topic.title()}")
        labels = article_data.get("labels", ["Umum"])
        html_content = article_data.get("html_content", "")
        image_prompt = article_data.get("image_prompt", topic)

        # 2. Generate Thumbnail Gambar
        image_info = gemini_service.generate_thumbnail(image_prompt, topic)

        # 3. Publikasikan ke Blogger
        blogger_service.publish_post(
            title=title,
            labels=labels,
            html_content=html_content,
            image_info=image_info
        )

        # 4. Beri kabar gembira ke WhatsApp pengirim
        success_msg = (
            f"✅ *ARTIKEL BERHASIL DIPUBLIKASIKAN!*\n\n"
            f"📌 *Judul:* {title}\n"
            f"🏷️ *Label/Kategori:* {', '.join(labels)}\n"
            f"🖼️ *Thumbnail:* Otomatis terpasang di cover tema Median UI!\n\n"
            f"Silakan periksa blog Anda sekarang. 🎉"
        )
        whatsapp_service.send_message(sender, success_msg)
        logger.info(f"Selesai! Artikel '{title}' telah terbit.")

    except Exception as e:
        logger.error(f"Error saat memproses artikel: {e}", exc_info=True)
        error_msg = (
            f"❌ *GAGAL MEMPROSES ARTIKEL*\n\n"
            f"Terjadi kesalahan saat memproses topik '{topic}':\n"
            f"_{str(e)}_\n\n"
            f"Silakan periksa konfigurasi API Key atau email Blogger Anda."
        )
        whatsapp_service.send_message(sender, error_msg)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <head>
            <title>WA-Blogger AI Bot Active</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; }
                .card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); text-align: center; max-width: 500px; }
                h1 { color: #38bdf8; margin-bottom: 10px; }
                p { color: #94a3b8; line-height: 1.6; }
                .badge { display: inline-block; background: #10b981; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🤖 Bot WhatsApp Blogger AI</h1>
                <p>Server bot aktif 24 jam dan siap menerima perintah generate & posting artikel ke tema Median UI Blogger Anda.</p>
                <div class="badge">● STATUS: ONLINE 24/7</div>
            </div>
        </body>
    </html>
    """

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "gemini_model": config.GEMINI_MODEL,
        "blogger_configured": blogger_service.is_configured(),
        "fonnte_configured": bool(config.FONNTE_TOKEN)
    }

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint Webhook untuk menerima pesan dari gateway WhatsApp (Fonnte, Wablas, dll).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    logger.info(f"Pesan webhook diterima: {body}")

    # Ekstraksi informasi pengirim dan isi pesan dari berbagai format gateway
    sender = body.get("sender") or body.get("from") or body.get("phone") or ""
    message = body.get("message") or body.get("text") or body.get("body") or ""

    if not message:
        return JSONResponse({"status": "ignored", "reason": "Pesan kosong"})

    # Bersihkan nomor sender (misal: "628123456789@s.whatsapp.net" -> "628123456789")
    clean_sender = sender.split("@")[0].strip()

    # Validasi Owner jika OWNER_NUMBER disetel di konfigurasi
    if config.OWNER_NUMBER and clean_sender != config.OWNER_NUMBER.strip():
        logger.warning(f"Akses ditolak untuk nomor bukan owner: {clean_sender}")
        return JSONResponse({"status": "forbidden", "reason": "Nomor tidak terdaftar sebagai pemilik"})

    text = message.strip()
    cmd = text.lower()

    # Perintah: Bantuan (!menu / !help)
    if cmd in ["!menu", "!help", "/menu", "/help"]:
        help_text = (
            "🤖 *PANDUAN BOT WHATSAPP BLOGGER AI*\n\n"
            "Gunakan perintah berikut untuk posting artikel otomatis:\n\n"
            "👉 *!tulis <topik artikel>*\n"
            "Contoh: `!tulis 7 tips merawat laptop agar tidak cepat panas`\n\n"
            "👉 *!status*\n"
            "Mengecek status kesiapan bot dan koneksi ke Blogger.\n\n"
            "✨ *Fitur Otomatis:*\n"
            "• Menulis artikel SEO berbobot dengan Gemini AI\n"
            "• Menyesuaikan format HTML khusus template Median UI\n"
            "• Membuat gambar thumbnail otomatis\n"
            "• Menerbitkan langsung ke Blogger!"
        )
        whatsapp_service.send_message(clean_sender, help_text)
        return JSONResponse({"status": "success", "reply": "Menu sent"})

    # Perintah: Cek Status (!status / !ping)
    if cmd in ["!status", "!ping", "/status", "/ping"]:
        cfg_status = "✅ Siap" if blogger_service.is_configured() else "⚠️ Belum Lengkap"
        status_text = (
            f"📊 *STATUS SERVER BOT*\n\n"
            f"• Kondisi: *Online 24/7*\n"
            f"• AI Model: *{config.GEMINI_MODEL}*\n"
            f"• Koneksi Blogger: *{cfg_status}*\n"
            f"• Server Respons: *Cepat (FastAPI)*"
        )
        whatsapp_service.send_message(clean_sender, status_text)
        return JSONResponse({"status": "success", "reply": "Status sent"})

    # Perintah: Tulis Artikel (!tulis <topik> atau /tulis <topik>)
    if cmd.startswith("!tulis") or cmd.startswith("/tulis"):
        # Ambil topik setelah kata perintah
        parts = text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            whatsapp_service.send_message(clean_sender, "⚠️ Format salah! Sertakan topik yang ingin ditulis.\nContoh: `!tulis cara merawat mobil matic`")
            return JSONResponse({"status": "bad_request"})

        topic = parts[1].strip()

        # Beri respon awal instan bahwa bot sudah menerima perintah
        wait_text = (
            f"⏳ *PERINTAH DITERIMA!*\n\n"
            f"Sedang meracik artikel SEO dan gambar thumbnail untuk topik:\n"
            f"👉 *\"{topic}\"*\n\n"
            f"Proses ini memakan waktu sekitar 15-30 detik. Notifikasi akan dikirimkan begitu artikel selesai terbit!"
        )
        whatsapp_service.send_message(clean_sender, wait_text)

        # Jalankan pembuatan dan publikasi di latar belakang (Background Tasks)
        background_tasks.add_task(process_and_publish_article, clean_sender, topic)

        return JSONResponse({"status": "processing", "topic": topic})

    return JSONResponse({"status": "ignored", "reason": "Bukan perintah yang dikenali"})

@app.post("/manual-post")
async def manual_post(topic: str, background_tasks: BackgroundTasks):
    """
    Endpoint manual untuk testing langsung via Browser/Postman tanpa WhatsApp
    """
    background_tasks.add_task(process_and_publish_article, "admin", topic)
    return {"status": "started", "topic": topic, "message": "Proses artikel dimulai di background."}
