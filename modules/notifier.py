# modules/notifier.py
# প্রতিটি step-এ Telegram-এ notification পাঠায়

import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send(message: str, video_path: str = None, silent: bool = False):
    """
    Telegram-এ message পাঠায়।
    video_path দিলে thumbnail-ও পাঠাবে।
    """
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return  # Token নেই, চুপ থাকো

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_notification": silent
        }, timeout=10)
    except:
        pass  # Notification fail হলেও main কাজ থামবে না


def send_photo(image_path: str, caption: str = ""):
    """Thumbnail বা image পাঠায়"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, "rb") as f:
            requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }, files={"photo": f}, timeout=20)
    except:
        pass


def send_video_preview(video_path: str, caption: str = ""):
    """ছোট video preview পাঠায়"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        with open(video_path, "rb") as f:
            requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }, files={"video": f}, timeout=120)
    except:
        pass


# ── Shortcut functions ──────────────────────────────────────

def notify_start(topic: str):
    send(
        f"🎬 <b>নতুন ভিডিও শুরু হয়েছে!</b>\n\n"
        f"📌 Topic: <code>{topic}</code>\n"
        f"⏳ Pipeline চলছে..."
    )

def notify_script_done(title: str, scene_count: int):
    send(
        f"📝 <b>Script তৈরি হয়েছে!</b>\n\n"
        f"🎯 Title: {title}\n"
        f"🎞️ Scenes: {scene_count}টি"
    )

def notify_images_done(count: int):
    send(f"🎨 <b>{count}টি AI Image তৈরি হয়েছে!</b>", silent=True)

def notify_thumbnail_done(thumbnail_path: str, title: str):
    send_photo(thumbnail_path, f"🖼️ <b>Thumbnail ready!</b>\n{title}")

def notify_voice_done():
    send("🎤 <b>Voiceover তৈরি হয়েছে!</b>", silent=True)

def notify_music_done(music_name: str):
    send(f"🎵 <b>Music ready:</b> {music_name}", silent=True)

def notify_video_done(video_path: str):
    size_mb = round(os.path.getsize(video_path) / (1024*1024), 1)
    send(
        f"🎬 <b>Video তৈরি হয়েছে!</b>\n\n"
        f"📁 Size: {size_mb} MB\n"
        f"⏳ Upload হচ্ছে..."
    )

def notify_uploaded(title: str, url: str):
    send(
        f"🎉 <b>YouTube Upload সম্পন্ন!</b>\n\n"
        f"📹 {title}\n\n"
        f"🔗 {url}\n\n"
        f"⚠️ এখন <b>Private</b> আছে। দেখে Public করুন!"
    )

def notify_error(step: str, error: str):
    send(
        f"❌ <b>Error হয়েছে!</b>\n\n"
        f"📍 Step: {step}\n"
        f"🔴 Error: <code>{str(error)[:200]}</code>"
    )

def notify_schedule_status(next_run: str):
    send(
        f"⏰ <b>Daily Schedule চালু আছে</b>\n\n"
        f"🕐 পরবর্তী ভিডিও: {next_run}",
        silent=True
    )
