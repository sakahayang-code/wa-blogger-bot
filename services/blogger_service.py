import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from config import config

logger = logging.getLogger(__name__)

class BloggerService:
    def __init__(self):
        self.blogger_email = config.BLOGGER_EMAIL
        self.gmail_user = config.GMAIL_USER
        self.gmail_password = config.GMAIL_APP_PASSWORD

    def is_configured(self) -> bool:
        """Memeriksa apakah konfigurasi email pengirim dan penerima Blogger sudah diisi"""
        return bool(self.blogger_email and self.gmail_user and self.gmail_password)

    def publish_post(self, title: str, labels: list, html_content: str, image_info: dict) -> bool:
        """
        Mempublikasikan artikel ke Blogger via fitur Mail-to-Blogger.
        Blogger secara otomatis:
        - Membaca [label1, label2] pada subjek email sebagai Kategori/Label.
        - Membaca gambar pertama <img> di awal bodi artikel sebagai Thumbnail/Featured Image
          (sangat krusial untuk template Median UI).
        """
        if not self.is_configured():
            err_msg = "Konfigurasi BLOGGER_EMAIL, GMAIL_USER, atau GMAIL_APP_PASSWORD belum lengkap di .env!"
            logger.error(err_msg)
            raise ValueError(err_msg)

        # Format subjek email untuk Blogger: "Judul Postingan [Label1, Label2]"
        labels_str = ", ".join(labels) if labels else "Umum"
        subject = f"{title} [{labels_str}]"

        # Buat kontainer email MIME
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = self.blogger_email

        # Susun gambar thumbnail di bagian paling atas konten (agar dideteksi oleh Median UI)
        thumbnail_html = ""
        cid_name = "post_thumbnail_img"

        if image_info.get("bytes"):
            # Jika gambar berasal dari Imagen 3 (binary bytes)
            thumbnail_html = f'''
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="cid:{cid_name}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);" />
            </div>
            '''
        elif image_info.get("url"):
            # Jika gambar berupa direct URL (fallback)
            thumbnail_html = f'''
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{image_info['url']}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);" />
            </div>
            '''

        # Gabungkan thumbnail di baris teratas dengan isi artikel HTML
        full_html = f"{thumbnail_html}\n{html_content}"

        # Pasang bodi HTML
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(full_html, "html", "utf-8"))

        # Jika ada image bytes, lampirkan sebagai inline MIME image
        if image_info.get("bytes"):
            img_part = MIMEImage(image_info["bytes"], _subtype="jpeg")
            img_part.add_header("Content-ID", f"<{cid_name}>")
            img_part.add_header("Content-Disposition", "inline", filename="thumbnail.jpg")
            msg.attach(img_part)

        # Kirim melalui SMTP Gmail SSL Port 465
        logger.info(f"Mengirim artikel ke Blogger ({self.blogger_email}) via SMTP Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.gmail_user, self.gmail_password)
            server.sendmail(self.gmail_user, self.blogger_email, msg.as_string())

        logger.info(f"Artikel '{title}' berhasil dikirim ke Blogger!")
        return True

blogger_service = BloggerService()
