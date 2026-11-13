import os
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
        self.blog_id = os.getenv("BLOGGER_BLOG_ID", "")

    def is_configured(self) -> bool:
        """Memeriksa apakah salah satu metode (Email atau Google API) sudah disetel"""
        has_email = bool(self.blogger_email and self.gmail_user and self.gmail_password)
        has_api = bool(self.blog_id and (os.path.exists("service_account.json") or os.path.exists("token.json")))
        return has_email or has_api

    def publish_post(self, title: str, labels: list, html_content: str, image_info: dict) -> bool:
        """
        Mempublikasikan artikel ke Blogger:
        - Prioritas 1: Google Blogger API v3 Resmi (jika ada BLOGGER_BLOG_ID & file credentials)
        - Prioritas 2: Mail-to-Blogger via SMTP Gmail
        """
        # Susun thumbnail di baris pertama bodi artikel agar dikenali tema Median UI
        thumbnail_html = ""
        cid_name = "post_thumbnail_img"

        if image_info.get("bytes"):
            # Jika menggunakan binary image bytes
            thumbnail_html = f'''
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="cid:{cid_name}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);" />
            </div>
            '''
        elif image_info.get("url"):
            # Jika menggunakan URL gambar
            thumbnail_html = f'''
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 25px;">
                <img border="0" src="{image_info['url']}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);" />
            </div>
            '''

        full_html = f"{thumbnail_html}\n{html_content}"

        # Cek apakah menggunakan Blogger API v3
        if self.blog_id and (os.path.exists("service_account.json") or os.path.exists("token.json")):
            return self._publish_via_api(title, labels, full_html)

        # Fallback ke Mail-to-Blogger
        return self._publish_via_email(title, labels, full_html, image_info, cid_name)

    def _publish_via_api(self, title: str, labels: list, full_html: str) -> bool:
        """Publikasi menggunakan Google Blogger API v3 Resmi"""
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        logger.info(f"Mempublikasikan '{title}' via Google Blogger API v3...")
        SCOPES = ['https://www.googleapis.com/auth/blogger']
        
        credentials = service_account.Credentials.from_service_account_file(
            "service_account.json", scopes=SCOPES
        )
        service = build('blogger', 'v3', credentials=credentials)
        
        post_body = {
            'kind': 'blogger#post',
            'title': title,
            'content': full_html,
            'labels': labels
        }
        
        result = service.posts().insert(blogId=self.blog_id, body=post_body, isDraft=False).execute()
        logger.info(f"Artikel berhasil terbit via Blogger API! URL: {result.get('url')}")
        return True

    def _publish_via_email(self, title: str, labels: list, full_html: str, image_info: dict, cid_name: str) -> bool:
        """Publikasi menggunakan fitur Mail-to-Blogger (SMTP Gmail)"""
        if not (self.blogger_email and self.gmail_user and self.gmail_password):
            err_msg = (
                "Konfigurasi Blogger belum lengkap!\n"
                "Silakan isi BLOGGER_EMAIL & GMAIL_APP_PASSWORD di .env, "
                "atau gunakan Blogger API dengan BLOGGER_BLOG_ID + service_account.json."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        labels_str = ", ".join(labels) if labels else "Umum"
        subject = f"{title} [{labels_str}]"

        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = self.blogger_email

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(full_html, "html", "utf-8"))

        if image_info.get("bytes"):
            img_part = MIMEImage(image_info["bytes"], _subtype="jpeg")
            img_part.add_header("Content-ID", f"<{cid_name}>")
            img_part.add_header("Content-Disposition", "inline", filename="thumbnail.jpg")
            msg.attach(img_part)

        logger.info(f"Mengirim artikel ke Blogger ({self.blogger_email}) via SMTP Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.gmail_user, self.gmail_password)
            server.sendmail(self.gmail_user, self.blogger_email, msg.as_string())

        logger.info(f"Artikel '{title}' berhasil dikirim ke Blogger via email!")
        return True

blogger_service = BloggerService()
