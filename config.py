import os
from dotenv import load_dotenv

# Membaca environment variable dari file .env (jika ada)
load_dotenv()

class Config:
    # Port untuk server FastAPI
    PORT = int(os.getenv("PORT", 8000))
    
    # Google Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # Model default, jika custom 'gemini-3.8-flash-high' belum tersedia publik di endpoint akun,
    # sistem otomatis fallback ke 'gemini-2.5-flash' atau 'gemini-2.0-flash'
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Mail-to-Blogger Credentials
    # Didapat dari: Dashboard Blogger -> Setelan -> Email -> "Publikasikan postingan menggunakan email"
    BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL", "")
    
    # Akun Gmail pengirim & Google App Password (16 digit)
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    
    # WhatsApp Gateway (Fonnte / Wablas)
    FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "")
    
    # Nomor WhatsApp Owner yang diizinkan (opsional untuk keamanan)
    # Kosongkan jika ingin bisa dipakai oleh nomor manapun
    OWNER_NUMBER = os.getenv("OWNER_NUMBER", "")

config = Config()
