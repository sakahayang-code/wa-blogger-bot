import logging
import requests
from config import config

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.fonnte_token = config.FONNTE_TOKEN

    def send_message(self, target: str, message: str) -> bool:
        """
        Mengirim balasan pesan WhatsApp ke pengirim melalui WhatsApp Gateway (Fonnte).
        Jika token belum disetel, pesan akan dicatat di log server.
        """
        if not self.fonnte_token:
            logger.info(f"[LOG SIMULASI WA -> {target}]:\n{message}")
            return True

        url = "https://api.fonnte.com/send"
        headers = {
            "Authorization": self.fonnte_token
        }
        payload = {
            "target": target,
            "message": message,
            "countryCode": "62"  # Kode negara Indonesia
        }

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=15)
            logger.info(f"Kirim balasan WA ke {target}: status {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Gagal mengirim balasan WhatsApp ke {target}: {e}")
            return False

whatsapp_service = WhatsAppService()
