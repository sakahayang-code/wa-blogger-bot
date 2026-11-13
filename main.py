import logging
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Query
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

def execute_publish(sender: str, topic: str):
    """
    Eksekusi pembuatan artikel dan penerbitan ke Blogger.
    Mengembalikan data artikel jika sukses.
    """
    logger.info(f"Mulai memproses topik: '{topic}' untuk pengirim: {sender}")
    
    # 1. Generate Artikel dengan Gemini
    article_data = gemini_service.generate_article(topic)
    title = article_data.get("title", f"Artikel: {topic.title()}")
    labels = article_data.get("labels", ["Umum"])
    html_content = article_data.get("html_content", "")
    image_prompt = article_data.get("image_prompt", topic)

    # 2. Generate Thumbnail Gambar (Imagen 3 / fallback)
    image_info = gemini_service.generate_thumbnail(image_prompt, topic)

    # 3. Publikasikan ke Blogger (API v3 atau Mail-to-Blogger)
    blogger_service.publish_post(
        title=title,
        labels=labels,
        html_content=html_content,
        image_info=image_info
    )

    success_msg = (
        f"✅ *ARTIKEL BERHASIL DIPUBLIKASIKAN!*\n\n"
        f"📌 *Judul:* {title}\n"
        f"🏷️ *Label/Kategori:* {', '.join(labels)}\n"
        f"🖼️ *Thumbnail:* Otomatis terpasang di cover tema Median UI!\n\n"
        f"Silakan periksa blog Anda sekarang. 🎉"
    )
    return title, labels, success_msg

def process_and_publish_article(sender: str, topic: str):
    """Fungsi latar belakang (Background Task)"""
    try:
        _, _, success_msg = execute_publish(sender, topic)
        whatsapp_service.send_message(sender, success_msg)
        logger.info(f"Selesai! Notifikasi terkirim ke WhatsApp.")
    except Exception as e:
        logger.error(f"Error saat memproses artikel: {e}", exc_info=True)
        error_msg = (
            f"❌ *GAGAL MEMPROSES ARTIKEL*\n\n"
            f"Terjadi kesalahan saat memproses topik '{topic}':\n"
            f"_{str(e)}_\n\n"
            f"Silakan periksa konfigurasi API Key atau Blogger Anda."
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
                <h1>🤖 Bot WhatsApp Blogger AI (Termux Ready)</h1>
                <p>Server bot aktif dan siap menerima perintah generate & posting artikel ke tema Median UI Blogger Anda.</p>
                <div class="badge">● STATUS: ONLINE (TERMUX / LOCALHOST)</div>
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
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Setel true jika menggunakan AutoResponder for WA agar balasan langsung terkirim")
):
    """
    Endpoint Webhook untuk menerima pesan dari WhatsApp:
    - Kompatibel dengan AutoResponder for WA di Android (Termux localhost:8000)
    - Kompatibel dengan MacroDroid di Android
    - Kompatibel dengan Gateway Webhook
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    logger.info(f"Pesan webhook diterima: {body}")

    # Ekstraksi field sender dan message dari berbagai format payload Android / Gateway
    sender = (
        body.get("sender") or
        body.get("from") or
        body.get("phone") or
        body.get("senderName") or
        "user"
    )
    message = (
        body.get("message") or
        body.get("text") or
        body.get("body") or
        body.get("queryText") or
        ""
    )

    if not message:
        return JSONResponse({"status": "ignored", "reason": "Pesan kosong"})

    clean_sender = str(sender).split("@")[0].strip()

    # Validasi Owner jika disetel
    if config.OWNER_NUMBER and clean_sender != config.OWNER_NUMBER.strip() and clean_sender != "user":
        logger.warning(f"Akses ditolak untuk nomor bukan owner: {clean_sender}")
        return JSONResponse({"status": "forbidden", "reply": "Akses ditolak: Hanya pemilik yang diizinkan."})

    text = message.strip()
    cmd = text.lower()

    # 1. Bantuan (!menu / !help)
    if cmd in ["!menu", "!help", "/menu", "/help"]:
        help_text = (
            "🤖 *PANDUAN BOT WHATSAPP BLOGGER AI*\n\n"
            "Gunakan perintah berikut:\n\n"
            "👉 *!tulis <topik artikel>*\n"
            "Contoh: `!tulis 7 tips merawat laptop agar tidak cepat panas`\n\n"
            "👉 *!status*\n"
            "Mengecek status kesiapan bot dan koneksi Blogger.\n\n"
            "✨ *Otomatis:* Artikel SEO + Thumbnail 16:9 + Format Median UI langsung terbit!"
        )
        whatsapp_service.send_message(clean_sender, help_text)
        return JSONResponse({"status": "success", "reply": help_text})

    # 2. Cek Status (!status / !ping)
    if cmd in ["!status", "!ping", "/status", "/ping"]:
        cfg_status = "✅ Siap" if blogger_service.is_configured() else "⚠️ Periksa Pengaturan"
        status_text = (
            f"📊 *STATUS BOT (TERMUX)*\n\n"
            f"• Kondisi: *Online di Android*\n"
            f"• AI Model: *{config.GEMINI_MODEL}*\n"
            f"• Blogger: *{cfg_status}*\n"
            f"• Template: *Median UI Ready*"
        )
        whatsapp_service.send_message(clean_sender, status_text)
        return JSONResponse({"status": "success", "reply": status_text})

    # 3. Perintah Tulis Artikel (!tulis <topik>)
    if cmd.startswith("!tulis") or cmd.startswith("/tulis"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            msg_err = "⚠️ Format salah! Sertakan topik yang ingin ditulis.\nContoh: `!tulis cara merawat mobil matic`"
            whatsapp_service.send_message(clean_sender, msg_err)
            return JSONResponse({"status": "bad_request", "reply": msg_err})

        topic = parts[1].strip()

        # Jika mode sync (misal AutoResponder for WA di Android)
        # Menghasilkan artikel langsung dan mengembalikan pesan ke AutoResponder
        if sync:
            try:
                _, _, success_msg = execute_publish(clean_sender, topic)
                return JSONResponse({"status": "success", "reply": success_msg})
            except Exception as e:
                err_reply = f"❌ Gagal memposting artikel: {e}"
                return JSONResponse({"status": "error", "reply": err_reply})

        # Jika mode async background
        wait_text = (
            f"⏳ *PERINTAH DITERIMA!*\n\n"
            f"Sedang meracik artikel SEO dan gambar thumbnail untuk topik:\n"
            f"👉 *\"{topic}\"*\n\n"
            f"Mohon tunggu sebentar, artikel sedang dipublikasikan..."
        )
        whatsapp_service.send_message(clean_sender, wait_text)
        background_tasks.add_task(process_and_publish_article, clean_sender, topic)

        return JSONResponse({"status": "processing", "reply": wait_text, "topic": topic})

    return JSONResponse({"status": "ignored", "reason": "Bukan perintah yang dikenali"})

@app.post("/manual-post")
async def manual_post(topic: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_and_publish_article, "admin", topic)
    return {"status": "started", "topic": topic, "message": "Proses artikel dimulai di background."}
