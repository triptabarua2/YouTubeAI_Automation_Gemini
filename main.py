#!/usr/bin/env python3
# main.py — পুরো pipeline চালায়
# এক command-এ Topic → Script → Images → Voice → Video → Upload

import os
import sys
import json
import argparse
import datetime
import shutil

# Modules
from modules.script_generator import generate_script, get_trending_topic
from modules.image_generator import generate_all_scene_images, generate_thumbnail
from modules.voiceover import generate_all_voiceovers
from modules.music_manager import get_music_for_video
from modules.video_editor import create_video
from modules.youtube_uploader import upload_video
from modules import notifier

TEMP_DIR = "temp"
OUTPUT_DIR = "output"
LOG_FILE = "video_log.json"


def clean_temp():
    """Temp files মুছে দেয়"""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(f"{TEMP_DIR}/images", exist_ok=True)
    os.makedirs(f"{TEMP_DIR}/audio", exist_ok=True)


def save_log(topic: str, script_data: dict, video_url: str):
    """প্রতিটি video-র record রাখে"""
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)

    logs.append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": topic,
        "title": script_data.get("title", ""),
        "url": video_url,
        "status": "uploaded"
    })

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def run_pipeline(topic: str = None, auto_upload: bool = False):
    """
    পুরো pipeline চালায়।
    topic=None হলে AI নিজেই topic বেছে নেবে।
    """
    print("\n" + "="*60)
    print("🎬  YouTube AI — Full Pipeline শুরু হচ্ছে")
    print("="*60)

    # Temp পরিষ্কার
    clean_temp()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── STEP 1: Topic ──
    if not topic:
        print("\n[1/7] 💡 AI topic বেছে নিচ্ছে...")
        topic = get_trending_topic()
    else:
        print(f"\n[1/7] 💡 Topic: {topic}")

    notifier.notify_start(topic)

    # ── STEP 2: Script ──
    print(f"\n[2/7] 📝 Script তৈরি হচ্ছে...")
    try:
        script_data = generate_script(topic)
    except Exception as e:
        notifier.notify_error("Script Generation", e)
        raise

    script_file = os.path.join(OUTPUT_DIR, "script.json")
    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    scenes = script_data["scenes"]
    notifier.notify_script_done(script_data.get("title", ""), len(scenes))

    # ── STEP 3: Images ──
    print(f"\n[3/7] 🎨 AI Images তৈরি হচ্ছে ({len(scenes)}টি)...")
    try:
        image_paths = generate_all_scene_images(scenes)
        notifier.notify_images_done(len(image_paths))
    except Exception as e:
        notifier.notify_error("Image Generation", e)
        raise

    # Thumbnail
    print(f"  🖼️ Thumbnail তৈরি হচ্ছে...")
    thumbnail_path = generate_thumbnail(
        script_data.get("thumbnail_prompt", topic),
        script_data.get("title", topic)
    )
    notifier.notify_thumbnail_done(thumbnail_path, script_data.get("title", ""))

    # ── STEP 4: Music ──
    print(f"\n[4/7] 🎵 Background music আনা হচ্ছে...")
    try:
        music_path = get_music_for_video(script_data)
        if music_path:
            notifier.notify_music_done(os.path.basename(music_path))
    except Exception as e:
        notifier.notify_error("Music", e)
        music_path = None

    # ── STEP 5: Voiceover ──
    print(f"\n[5/7] 🎤 Voiceover তৈরি হচ্ছে...")
    try:
        audio_paths = generate_all_voiceovers(scenes)
        notifier.notify_voice_done()
    except Exception as e:
        notifier.notify_error("Voiceover", e)
        raise

    # ── STEP 6: Video Edit ──
    print(f"\n[6/7] 🎬 Video তৈরি হচ্ছে...")
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"video_{timestamp}.mp4"
        video_path = create_video(scenes, image_paths, audio_paths, output_filename, music_path)
        notifier.notify_video_done(video_path)
    except Exception as e:
        notifier.notify_error("Video Editing", e)
        raise

    # ── STEP 7: Upload ──
    video_url = ""
    if auto_upload:
        print(f"\n[7/7] 📤 YouTube-এ upload হচ্ছে...")
        try:
            video_url = upload_video(video_path, thumbnail_path, script_data)
            notifier.notify_uploaded(script_data.get("title", ""), video_url)
        except Exception as e:
            notifier.notify_error("YouTube Upload", e)
            raise
    else:
        print(f"\n[7/7] ⏸️  Upload Skip")
        print(f"  Video ready: {video_path}")
        notifier.send(
            f"✅ <b>Video তৈরি হয়েছে!</b>\n\n"
            f"📹 {script_data.get('title', '')}\n\n"
            f"⚠️ Auto-upload বন্ধ ছিল।\nManually upload করুন।"
        )

    # Log সেভ
    save_log(topic, script_data, video_url)

    # Summary
    print("\n" + "="*60)
    print("🎉  Pipeline সম্পন্ন!")
    print("="*60)
    print(f"📹 Topic:   {topic}")
    print(f"📝 Title:   {script_data.get('title', '')}")
    print(f"📁 Video:   {video_path}")
    if video_url:
        print(f"🌐 URL:     {video_url}")
    print("="*60 + "\n")

    return video_path, script_data


def show_logs():
    """কতগুলো video বানানো হয়েছে দেখায়"""
    if not os.path.exists(LOG_FILE):
        print("এখনো কোনো video তৈরি হয়নি।")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    print(f"\n📊 মোট {len(logs)}টি video তৈরি হয়েছে:\n")
    for log in logs[-10:]:  # Last 10
        print(f"  📅 {log['date']} | {log['title']}")
        if log.get('url'):
            print(f"     🔗 {log['url']}")


# ============================================================
#  Command Line Interface
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube AI — Full Automation")
    parser.add_argument("--topic", type=str, help="ভিডিওর বিষয় (না দিলে AI নিজে বাছবে)")
    parser.add_argument("--auto-upload", action="store_true", help="Automatically YouTube-এ upload করবে")
    parser.add_argument("--logs", action="store_true", help="পুরনো video-র list দেখাবে")
    parser.add_argument("--schedule", action="store_true", help="Daily schedule mode চালু করবে")

    args = parser.parse_args()

    if args.logs:
        show_logs()

    elif args.schedule:
        import schedule
        import time
        from config import UPLOAD_TIME

        def daily_job():
            print(f"\n⏰ Daily job শুরু হচ্ছে...")
            run_pipeline(auto_upload=True)

        schedule.every().day.at(UPLOAD_TIME).do(daily_job)
        print(f"⏰ Daily schedule চালু! প্রতিদিন {UPLOAD_TIME}-এ video তৈরি হবে।")
        print("বন্ধ করতে Ctrl+C চাপুন।\n")

        while True:
            schedule.run_pending()
            time.sleep(60)

    else:
        run_pipeline(
            topic=args.topic,
            auto_upload=args.auto_upload
        )
