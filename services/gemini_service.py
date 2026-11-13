import json
import logging
import base64
import urllib.parse
import requests
from config import config

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_candidates = [
            config.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]

    def generate_article(self, topic: str) -> dict:
        """
        Menghasilkan artikel SEO format HTML untuk Median UI
        menggunakan REST API resmi Google Gemini (tanpa pydantic / tanpa rust).
        """
        api_key = config.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY belum disetel di file .env!")

        prompt = f"""
Kamu adalah seorang Master Content Creator dan Pakar SEO Blogger profesional.
Tugasmu adalah membuat sebuah artikel blog yang sangat menarik, mendalam, orisinal, dan lengkap berdasarkan topik berikut:
"{topic}"

Formatkan hasilnya dalam JSON VALID dengan struktur persis seperti berikut:
{{
  "title": "Judul Artikel Menarik & SEO-Friendly (Maksimal 65 karakter, tanpa tanda petik)",
  "labels": ["Label1", "Label2", "Label3"],
  "meta_description": "Deskripsi singkat SEO untuk cuplikan pencarian Google (140-160 karakter)",
  "image_prompt": "Deskripsi visual dalam Bahasa Inggris untuk thumbnail 16:9 yang profesional dan modern",
  "html_content": "Isi artikel lengkap dalam format tag HTML murni (Gunakan <h2>, <h3>, <p>, <ul>, <ol>, <blockquote>, dan kotak alert Median UI)"
}}

Panduan Konten HTML (Khusus Template Median UI):
1. JANGAN sertakan tag <html>, <head>, atau <body>, cukup isi bodinya saja.
2. Gunakan pembuka yang memikat pembaca di paragraf awal.
3. Gunakan sub-judul <h2> dan <h3> secara terstruktur untuk keterbacaan (Readability & TOC).
4. Sisipkan minimal satu kotak info/tips khas Median UI:
   <div class="alert alert-info"><strong>Tips Bermanfaat:</strong> [Teks tips/catatan penting]</div>
5. Sisipkan daftar rincian dengan <ul> atau <ol>.
6. Sertakan bagian Tanya Jawab (FAQ) singkat di akhir artikel sebelum kesimpulan:
   <div class="faq-item"><strong>T: [Pertanyaan Umum]?</strong><p>J: [Jawaban ringkas]</p></div>
7. Bahasa Indonesia yang mengalir, santun, baku namun tetap santai dan mudah dipahami.
8. Pastikan panjang artikel minimal 500 - 800 kata.

PENTING: Output HANYA JSON murni tanpa awalan ```json atau teks lain di luar kurung kurawal.
"""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7
            }
        }

        response_text = None
        last_error = None

        for model in self.model_candidates:
            if not model:
                continue
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                logger.info(f"Mengirim permintaan ke Gemini API via REST (Model: {model})...")
                res = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=45
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            response_text = parts[0].get("text", "").strip()
                            logger.info(f"Berhasil mendapatkan respon dari {model}!")
                            break
                else:
                    logger.warning(f"Model {model} HTTP {res.status_code}: {res.text[:200]}")
                    last_error = f"HTTP {res.status_code}: {res.text[:150]}"
            except Exception as e:
                logger.warning(f"Error memanggil {model}: {e}")
                last_error = e

        if not response_text:
            raise RuntimeError(f"Gagal generate artikel dengan Gemini: {last_error}")

        # Bersihkan format markdown ```json jika ada
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        try:
            result_json = json.loads(response_text)
        except json.JSONDecodeError:
            result_json = {
                "title": f"Panduan Lengkap: {topic.title()}",
                "labels": ["Informasi", "Tips"],
                "meta_description": f"Pelajari seluk beluk dan informasi seputar {topic} secara lengkap.",
                "image_prompt": f"Professional blog banner illustration about {topic}, 16:9 ratio, modern digital art",
                "html_content": f"<p>{response_text}</p>"
            }

        return result_json

    def generate_thumbnail(self, image_prompt: str, topic: str) -> dict:
        """
        Menghasilkan gambar thumbnail:
        1. Coba Imagen 3 via REST API.
        2. Fallback otomatis ke Pollinations AI jika Imagen 3 tidak aktif/limit.
        """
        api_key = config.GEMINI_API_KEY
        if api_key:
            try:
                logger.info("Mencoba membuat gambar via Google Imagen 3 REST API...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
                payload = {
                    "instances": [
                        {"prompt": f"{image_prompt}, high resolution blog thumbnail, 16:9, modern, sharp"}
                    ],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "16:9"
                    }
                }
                res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    preds = data.get("predictions", [])
                    if preds and "bytesBase64Encoded" in preds[0]:
                        img_bytes = base64.b64decode(preds[0]["bytesBase64Encoded"])
                        logger.info("Berhasil membuat thumbnail dengan Imagen 3!")
                        return {"bytes": img_bytes, "url": None}
            except Exception as e:
                logger.warning(f"Imagen 3 error: {e}. Menggunakan fallback gambar online...")

        # Fallback Pollinations AI
        clean_topic = urllib.parse.quote(f"{topic} professional blog banner modern 16:9")
        fallback_url = f"https://image.pollinations.ai/prompt/{clean_topic}?width=1280&height=720&nologo=true"
        return {"bytes": None, "url": fallback_url}

gemini_service = GeminiService()
