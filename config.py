import os

# Safe .env loader: Bekerja meskipun python-dotenv belum terpasang
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'\"")
                    os.environ.setdefault(key.strip(), val)

class Config:
    PORT = int(os.getenv("PORT", 8000))
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Blogger Email (Mail-to-Blogger)
    BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL", "")
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    
    # Blogger API v3 (Alternatif jika email tidak bisa di-save)
    BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "")
    
    # WhatsApp Gateway (Opsional jika pakai Fonnte)
    FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "")
    
    # Nomor WhatsApp Owner
    OWNER_NUMBER = os.getenv("OWNER_NUMBER", "")

config = Config()
