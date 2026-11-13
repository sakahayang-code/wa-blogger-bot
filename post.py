#!/usr/bin/env python3
"""
CLI Tool untuk Termux di Android.
Memungkinkan Anda generate dan posting artikel SEO + Thumbnail Median UI
langsung dari terminal Termux tanpa perlu membuka browser!

Cara pakai:
  python post.py "Topik Artikel Anda"
"""

import sys
import os

# Membaca konfigurasi (otomatis membaca .env)
from config import config
from services.gemini_service import gemini_service
from services.blogger_service import blogger_service

def main():
    if len(sys.argv) < 2:
        print("\n❌ Masukkan topik artikel yang ingin dibuat!")
        print("Penggunaan:")
        print("  python post.py \"topik artikel yang ingin ditulis\"\n")
        print("Contoh:")
        print("  python post.py \"cara merawat baterai smartphone agar awet\"\n")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    print(f"\n🚀 [TERMUX] Memulai pembuatan artikel untuk topik: '{topic}'")
    print(f"⏳ Menghubungi Google Gemini Flash AI (Model: {config.GEMINI_MODEL})...")

    try:
        # 1. Generate Artikel
        article_data = gemini_service.generate_article(topic)
        title = article_data.get("title", f"Artikel: {topic.title()}")
        labels = article_data.get("labels", ["Informasi"])
        html_content = article_data.get("html_content", "")
        image_prompt = article_data.get("image_prompt", topic)

        print(f"\n📌 Judul: {title}")
        print(f"🏷️  Label: {', '.join(labels)}")
        print(f"📝 Panjang Konten: {len(html_content)} karakter")

        # 2. Generate Thumbnail
        print("\n🎨 Membuat thumbnail 16:9 (Imagen 3 / Fallback)...")
        image_info = gemini_service.generate_thumbnail(image_prompt, topic)
        if image_info.get("bytes"):
            print("✅ Thumbnail Imagen 3 berhasil dibuat!")
        else:
            print(f"✅ Menggunakan Thumbnail URL: {image_info.get('url')[:60]}...")

        # 3. Publikasikan ke Blogger
        print("\n📤 Menerbitkan ke Blogger (Median UI)...")
        blogger_service.publish_post(
            title=title,
            labels=labels,
            html_content=html_content,
            image_info=image_info
        )

        print("\n" + "="*50)
        print("🎉 BERHASIL! Artikel telah dipublikasikan ke blog Anda!")
        print(f"📌 Judul: {title}")
        print("🖼️  Thumbnail: Otomatis tampil di cover depan tema Median UI!")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
