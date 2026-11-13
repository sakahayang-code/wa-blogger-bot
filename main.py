import logging
import threading
from flask import Flask, request, jsonify, Response
from config import config
from services.gemini_service import gemini_service
from services.blogger_service import blogger_service
from services.whatsapp_service import whatsapp_service

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("wa-blogger-bot")

app = Flask(__name__)

def execute_publish(sender: str, topic: str):
    """
    Eksekusi pembuatan artikel dan penerbitan ke Blogger.
    """
    logger.info(f"Mulai memproses topik: '{topic}' untuk: {sender}")
    
    # 1. Generate Artikel dengan Gemini REST API
    article_data = gemini_service.generate_article(topic)
    title = article_data.get("title", f"Artikel: {topic.title()}")
    labels = article_data.get("labels", ["Umum"])
    html_content = article_data.get("html_content", "")
    image_prompt = article_data.get("image_prompt", topic)

    # 2. Generate Thumbnail (Imagen 3 / fallback)
    image_info = gemini_service.generate_thumbnail(image_prompt, topic)

    # 3. Publikasikan ke Blogger
    blogger_service.publish_post(
        title=title,
        labels=labels,
        html_content=html_content,
        image_info=image_info
    )

    success_msg = (
        f"✅ *ARTIKEL BERHASIL DIPUBLIKASIKAN!*\n\n"
        f"📌 *Judul:* {title}\n"
        f"🏷️ *Label:* {', '.join(labels)}\n"
        f"🖼️ *Thumbnail:* Otomatis terpasang di cover tema Median UI!\n\n"
        f"Silakan periksa blog Anda sekarang. 🎉"
    )
    return title, labels, success_msg

def async_worker(sender: str, topic: str):
    """Worker background thread"""
    try:
        _, _, success_msg = execute_publish(sender, topic)
        whatsapp_service.send_message(sender, success_msg)
        logger.info(f"Selesai! Notifikasi sukses terkirim ke {sender}.")
    except Exception as e:
        logger.error(f"Error memproses artikel: {e}", exc_info=True)
        error_msg = f"❌ *GAGAL MEMPROSES ARTIKEL*\n\nError: _{str(e)}_"
        whatsapp_service.send_message(sender, error_msg)

@app.route("/", methods=["GET"])
def index():
    return """
    <html>
        <head>
            <title>WA-Blogger Bot Active</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; }
                .card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); text-align: center; max-width: 500px; }
                h1 { color: #38bdf8; margin-bottom: 10px; }
                p { color: #94a3b8; line-height: 1.6; }
                .badge { display: inline-block; background: #10b981; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🤖 Bot WhatsApp Blogger AI</h1>
                <p>Server bot aktif di Termux Android dan siap menerima perintah generate & posting artikel ke tema Median UI Blogger.</p>
                <div class="badge">● STATUS: ONLINE (TERMUX / FLASK)</div>
            </div>
        </body>
    </html>
    """

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "model": config.GEMINI_MODEL,
        "blogger_ready": blogger_service.is_configured()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    logger.info(f"Pesan webhook diterima: {data}")

    sender = data.get("sender") or data.get("from") or data.get("phone") or "user"
    message = data.get("message") or data.get("text") or data.get("body") or ""

    if not message:
        return jsonify({"status": "ignored", "reason": "Pesan kosong"})

    clean_sender = str(sender).split("@")[0].strip()

    # Validasi Owner jika diatur
    if config.OWNER_NUMBER and clean_sender != config.OWNER_NUMBER.strip() and clean_sender != "user":
        return jsonify({"status": "forbidden", "reply": "Akses ditolak: Hanya pemilik yang diizinkan."})

    text = message.strip()
    cmd = text.lower()

    # 1. Bantuan
    if cmd in ["!menu", "!help", "/menu", "/help"]:
        help_text = (
            "🤖 *PANDUAN BOT WHATSAPP BLOGGER AI*\n\n"
            "👉 *!tulis <topik artikel>*\n"
            "Contoh: `!tulis 7 tips merawat laptop agar tidak cepat panas`\n\n"
            "👉 *!status*\n"
            "Mengecek status kesiapan bot dan koneksi Blogger."
        )
        whatsapp_service.send_message(clean_sender, help_text)
        return jsonify({"status": "success", "reply": help_text})

    # 2. Status
    if cmd in ["!status", "!ping", "/status", "/ping"]:
        cfg_status = "✅ Siap" if blogger_service.is_configured() else "⚠️ Periksa .env"
        status_text = (
            f"📊 *STATUS BOT (TERMUX)*\n\n"
            f"• Kondisi: *Online di Android*\n"
            f"• AI Model: *{config.GEMINI_MODEL}*\n"
            f"• Blogger: *{cfg_status}*\n"
            f"• Engine: *Lightweight Flask (No Rust)*"
        )
        whatsapp_service.send_message(clean_sender, status_text)
        return jsonify({"status": "success", "reply": status_text})

    # 3. Tulis Artikel
    if cmd.startswith("!tulis") or cmd.startswith("/tulis"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            msg_err = "⚠️ Format salah! Sertakan topik yang ingin ditulis.\nContoh: `!tulis cara merawat mobil matic`"
            return jsonify({"status": "bad_request", "reply": msg_err})

        topic = parts[1].strip()
        is_sync = request.args.get("sync", "").lower() in ["true", "1"]

        # Jika mode sync (khusus AutoResponder for WA di Android)
        if is_sync:
            try:
                _, _, success_msg = execute_publish(clean_sender, topic)
                return jsonify({"status": "success", "reply": success_msg})
            except Exception as e:
                return jsonify({"status": "error", "reply": f"❌ Gagal memposting artikel: {e}"})

        # Mode background async
        wait_text = (
            f"⏳ *PERINTAH DITERIMA!*\n\n"
            f"Sedang meracik artikel SEO dan gambar thumbnail untuk topik:\n"
            f"👉 *\"{topic}\"*\n\n"
            f"Mohon tunggu sebentar, artikel sedang dipublikasikan..."
        )
        whatsapp_service.send_message(clean_sender, wait_text)
        threading.Thread(target=async_worker, args=(clean_sender, topic), daemon=True).start()

        return jsonify({"status": "processing", "reply": wait_text, "topic": topic})

    return jsonify({"status": "ignored", "reason": "Bukan perintah yang dikenali"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
