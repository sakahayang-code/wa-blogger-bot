import json
import logging
import urllib.parse
from google import genai
from google.genai import errors
from config import config

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # Model fallback cascade jika model utama belum tersedia
        self.model_candidates = [
            config.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]

    def _get_client(self):
        if not self.client and config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        return self.client

    def generate_article(self, topic: str):
        """
        Menghasilkan artikel blog lengkap, SEO-friendly, dan berformat HTML
        yang dioptimasi secara spesifik untuk template Median UI (Blogger).
        """
        client = self._get_client()
        if not client:
            raise ValueError("GEMINI_API_KEY belum disetel di konfigurasi atau file .env")

        prompt = f"""
Kamu adalah seorang Master Content Creator dan Pakar SEO Blogger profesional.
Tugasmu adalah membuat sebuah artikel blog yang sangat menarik, mendalam, orisinal, dan lengkap berdasarkan topik berikut:
"{topic}"

Formatkan hasilnya dalam JSON VALID dengan struktur persis seperti berikut:
{{
  "title": "Judul Artikel Menarik & SEO-Friendly (Maksimal 65 karakter, tanpa tanda petik)",
  "labels": ["Label1", "Label2", "Label3"],
  "meta_description": "Deskripsi singkat SEO untuk cuplikan pencarian Google (140-160 karakter)",
  "image_prompt": "Deskripsi visual dalam Bahasa Inggris untuk membuat gambar thumbnail 16:9 yang profesional, modern, relevan dengan topik",
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

        response_text = None
        last_error = None

        # Coba model utama, jika gagal coba kandidat fallback berikutnya
        for model in self.model_candidates:
            if not model:
                continue
            try:
                logger.info(f"Mencoba generate artikel dengan model: {model}")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    response_text = response.text.strip()
                    logger.info(f"Berhasil generate konten menggunakan model: {model}")
                    break
            except Exception as e:
                logger.warning(f"Gagal dengan model {model}: {e}")
                last_error = e
                continue

        if not response_text:
            raise RuntimeError(f"Gagal generate konten dengan semua model: {last_error}")

        # Bersihkan pembungkus markdown ```json ... ``` jika model menyertakannya
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback jika model gagal mengeluarkan JSON valid
            logger.warning("Gagal parsing JSON, menggunakan ekstraksi manual")
            data = {
                "title": f"Panduan Lengkap: {topic.title()}",
                "labels": ["Informasi", "Tips", "Tutorial"],
                "meta_description": f"Pelajari seluk beluk dan informasi penting seputar {topic} secara lengkap.",
                "image_prompt": f"Professional clean minimalist illustration about {topic}, modern digital art, high quality",
                "html_content": f"<p>{response_text}</p>"
            }

        return data

    def generate_thumbnail(self, image_prompt: str, topic: str):
        """
        Menghasilkan gambar thumbnail:
        1. Pertama mencoba Google Imagen 3 via Gemini API.
        2. Jika Imagen 3 limit/gagal, fallback otomatis ke URL ilustrasi Pollinations AI berkualitas tinggi.
        """
        client = self._get_client()
        image_bytes = None

        # 1. Coba Imagen 3
        if client:
            try:
                logger.info(f"Mencoba membuat thumbnail via Imagen 3...")
                result = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=f"{image_prompt}, high resolution, professional blog banner illustration, 16:9 ratio, vivid lighting, sharp focus",
                    config=dict(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        output_mime_type="image/jpeg"
                    )
                )
                if result and result.generated_images:
                    image_bytes = result.generated_images[0].image.image_bytes
                    logger.info("Berhasil membuat gambar via Imagen 3!")
                    return {"bytes": image_bytes, "url": None}
            except Exception as e:
                logger.warning(f"Imagen 3 tidak tersedia atau limit: {e}. Beralih ke fallback gambar online...")

        # 2. Fallback: URL ilustrasi cerdas (Pollinations AI)
        clean_prompt = urllib.parse.quote(f"{topic} professional blog banner modern aesthetic 16:9")
        fallback_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1280&height=720&nologo=true"
        logger.info(f"Menggunakan thumbnail fallback URL: {fallback_url}")
        
        return {"bytes": None, "url": fallback_url}

gemini_service = GeminiService()
