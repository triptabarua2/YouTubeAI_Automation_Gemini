#!/usr/bin/env python3
# main.py — Multi-Channel YouTube AI Pipeline
# ৩টি বাংলা channel — আলাদা topic, আলাদা upload time

import os
import sys
import json
import argparse
import datetime
import shutil

from modules.script_generator import generate_script, get_trending_topic
from modules.image_generator   import generate_all_scene_images, generate_thumbnail
from modules.voiceover         import generate_all_voiceovers, merge_all_language_tracks
from modules.music_manager     import get_music_for_video
from modules.video_editor      import create_video
from modules.youtube_uploader  import upload_video
from modules                   import notifier
from config                    import CHANNELS, SCENES_PER_VIDEO

OUTPUT_DIR = "output"
LOG_FILE   = "video_log.json"


def get_channel_config(channel_id: str) -> dict:
    """Channel config আনে। না থাকলে error।"""
    if channel_id not in CHANNELS:
        valid = ", ".join(CHANNELS.keys())
        raise ValueError(f"❌ Channel '{channel_id}' নেই। Valid: {valid}")
    return CHANNELS[channel_id]


def clean_temp(channel_id: str):
    """Channel-এর temp folder পরিষ্কার করে।"""
    temp_dir = f"temp/{channel_id}"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(f"{temp_dir}/images", exist_ok=True)
    os.makedirs(f"{temp_dir}/audio",  exist_ok=True)
    return temp_dir


def save_log(channel_id: str, topic: str, script_data: dict, video_url: str):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs.append({
        "date":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "channel":   channel_id,
        "topic":     topic,
        "title":     script_data.get("title", ""),
        "url":       video_url,
        "status":    "uploaded"
    })
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def run_pipeline(channel_id: str, topic: str = None, auto_upload: bool = False):
    """
    একটা channel-এর পুরো pipeline চালায়।
    """
    ch = get_channel_config(channel_id)

    print("\n" + "="*60)
    print(f"🎬  Channel: {ch['name']}")
    print(f"🎯  Type: {ch['topic']}")
    print("="*60)

    # Temp setup
    temp_dir = clean_temp(channel_id)
    channel_output = os.path.join(OUTPUT_DIR, channel_id)
    os.makedirs(channel_output, exist_ok=True)

    # ── STEP 1: Topic ──────────────────────────────────────────
    if not topic:
        print(f"\n[1/7] 💡 AI topic বেছে নিচ্ছে ({ch['topic']})...")
        topic = get_trending_topic(
            topic_type=ch["topic"],
            topic_description=ch["topic_description"]
        )
    else:
        print(f"\n[1/7] 💡 Topic: {topic}")

    notifier.notify_start(f"[{ch['name']}] {topic}")

    # ── STEP 2: Script ─────────────────────────────────────────
    print(f"\n[2/7] 📝 Script তৈরি হচ্ছে...")
    try:
        script_data = generate_script(
            topic=topic,
            channel_style=ch["style"],
            topic_type=ch["topic"]
        )
    except Exception as e:
        notifier.notify_error("Script", e); raise

    script_path = os.path.join(channel_output, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    scenes = script_data["scenes"]
    notifier.notify_script_done(script_data.get("title", ""), len(scenes))

    # ── STEP 3: Images ─────────────────────────────────────────
    print(f"\n[3/7] 🎨 AI Images তৈরি হচ্ছে ({len(scenes)}টি)...")
    try:
        image_paths = generate_all_scene_images(scenes, temp_dir=temp_dir, topic=ch["topic"])
        thumbnail_path = generate_thumbnail(
            script_data.get("thumbnail_prompt", topic),
            script_data.get("title", topic),
            temp_dir=temp_dir
        )
        notifier.notify_images_done(len(image_paths))
        notifier.notify_thumbnail_done(thumbnail_path, script_data.get("title", ""))
    except Exception as e:
        notifier.notify_error("Images", e); raise

    # ── STEP 4: Music ──────────────────────────────────────────
    print(f"\n[4/7] 🎵 Background music আনা হচ্ছে...")
    try:
        music_path = get_music_for_video(script_data)
        if music_path:
            notifier.notify_music_done(os.path.basename(music_path))
    except Exception as e:
        notifier.notify_error("Music", e)
        music_path = None

    # ── STEP 5: Voiceover ──────────────────────────────────────
    print(f"\n[5/7] 🎤 Voiceover তৈরি হচ্ছে (বাংলা + English + হিন্দি)...")
    try:
        all_audio_paths = generate_all_voiceovers(scenes, temp_dir=temp_dir)
        audio_tracks    = merge_all_language_tracks(all_audio_paths, temp_dir=temp_dir)
        audio_paths     = all_audio_paths["bn"]
        notifier.notify_voice_done()
    except Exception as e:
        notifier.notify_error("Voiceover", e); raise

    # ── STEP 6: Video ──────────────────────────────────────────
    print(f"\n[6/7] 🎬 Video তৈরি হচ্ছে...")
    try:
        timestamp       = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"{channel_id}_{timestamp}.mp4"
        video_path = create_video(
            scenes, image_paths, audio_paths,
            output_filename, music_path,
            output_dir=channel_output,
            topic=ch["topic"]
        )
        notifier.notify_video_done(video_path)
    except Exception as e:
        notifier.notify_error("Video", e); raise

    # ── STEP 7: Upload ─────────────────────────────────────────
    video_url = ""
    if auto_upload:
        print(f"\n[7/7] 📤 YouTube-এ upload হচ্ছে ({ch['name']})...")
        try:
            video_url = upload_video(
                video_path, thumbnail_path, script_data,
                audio_tracks=audio_tracks,
                client_secret=ch["client_secret"],
                token_file=ch["token_file"],
                category_id=ch["category_id"],
                language=ch["language"],
            )
            notifier.notify_uploaded(script_data.get("title", ""), video_url)
        except Exception as e:
            notifier.notify_error("Upload", e); raise
    else:
        print(f"\n[7/7] ⏸️  Upload skip — Video ready: {video_path}")
        notifier.send(
            f"✅ <b>[{ch['name']}] Video তৈরি!</b>\n\n"
            f"📹 {script_data.get('title','')}\n\n"
            f"⚠️ Auto-upload বন্ধ ছিল।"
        )

    save_log(channel_id, topic, script_data, video_url)

    print("\n" + "="*60)
    print(f"🎉  [{ch['name']}] Pipeline সম্পন্ন!")
    print(f"📁  Video: {video_path}")
    if video_url:
        print(f"🌐  URL: {video_url}")
    print("="*60 + "\n")

    return video_path, script_data


def show_logs(channel_id: str = None):
    if not os.path.exists(LOG_FILE):
        print("এখনো কোনো video তৈরি হয়নি।"); return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
    if channel_id:
        logs = [l for l in logs if l.get("channel") == channel_id]
    print(f"\n📊 মোট {len(logs)}টি video:\n")
    for log in logs[-15:]:
        ch_label = f"[{log.get('channel','')}] " if not channel_id else ""
        print(f"  📅 {log['date']} {ch_label}{log['title']}")
        if log.get("url"):
            print(f"     🔗 {log['url']}")


# ============================================================
#  Schedule Mode — ৩টা channel আলাদা সময়ে চলবে
# ============================================================

def run_schedule():
    import schedule
    import time

    print("⏰ Multi-Channel Schedule Mode চালু!\n")

    for ch_id, ch in CHANNELS.items():
        upload_time = ch["upload_time"]

        def make_job(cid):
            def job():
                print(f"\n⏰ [{CHANNELS[cid]['name']}] শুরু হচ্ছে...")
                try:
                    run_pipeline(cid, auto_upload=True)
                except Exception as e:
                    print(f"❌ [{cid}] Error: {e}")
            return job

        schedule.every().day.at(upload_time).do(make_job(ch_id))
        print(f"  ✅ {ch['name']} → প্রতিদিন {upload_time}-এ upload হবে")

    print("\nবন্ধ করতে Ctrl+C চাপুন.\n")
    while True:
        schedule.run_pending()
        time.sleep(60)


# ============================================================
#  CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube AI — Multi-Channel")
    parser.add_argument("--channel",     type=str, default=None,
                        help="channel_1 / channel_2 / channel_3")
    parser.add_argument("--topic",       type=str, default=None)
    parser.add_argument("--auto-upload", action="store_true")
    parser.add_argument("--logs",        action="store_true")
    parser.add_argument("--schedule",    action="store_true")
    parser.add_argument("--all",         action="store_true",
                        help="৩টা channel একসাথে চালাবে (একটার পর একটা)")
    args = parser.parse_args()

    if args.logs:
        show_logs(args.channel)

    elif args.schedule:
        run_schedule()

    elif args.all:
        # ৩টা channel একসাথে (একটার পর একটা)
        for ch_id in CHANNELS:
            print(f"\n{'='*60}")
            print(f"🚀 {ch_id} শুরু হচ্ছে...")
            try:
                run_pipeline(ch_id, auto_upload=args.auto_upload)
            except Exception as e:
                print(f"❌ {ch_id} failed: {e}")
                continue

    elif args.channel:
        run_pipeline(
            channel_id=args.channel,
            topic=args.topic,
            auto_upload=args.auto_upload
        )

    else:
        print("❓ Channel বলুন। উদাহরণ:")
        print("   python main.py --channel channel_1")
        print("   python main.py --channel channel_2 --auto-upload")
        print("   python main.py --all --auto-upload")
        print("   python main.py --schedule")
        print("\nAvailable channels:")
        for ch_id, ch in CHANNELS.items():
            print(f"  {ch_id}: {ch['name']} ({ch['topic']}) → {ch['upload_time']}")
