#!/usr/bin/env python3
# agent.py — Fully Autonomous YouTube AI Agent
# নিজে থেকে সব channel এর video বানাবে, upload করবে, retry করবে
# কোনো human input ছাড়াই 24/7 চলবে

import os
import sys
import json
import time
import random
import datetime
import traceback
import schedule
import threading

# ── Project imports ───────────────────────────────────────────
from config import CHANNELS
from main   import run_pipeline
from modules import notifier

# ── State file — agent কোথায় আছে মনে রাখে ──────────────────
STATE_FILE   = "agent_state.json"
LOG_FILE     = "agent_log.json"
MAX_RETRIES  = 3
RETRY_DELAY  = 300   # 5 মিনিট পরে retry
HEALTH_CHECK = 3600  # ১ ঘন্টা পরপর health check

# ═════════════════════════════════════════════════════════════
# State Management
# ═════════════════════════════════════════════════════════════

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "agent_started":  None,
        "total_videos":   0,
        "total_errors":   0,
        "channels":       {ch: {"videos_made": 0, "last_run": None,
                                "last_error": None, "consecutive_errors": 0}
                           for ch in CHANNELS}
    }

def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def log_event(event_type: str, channel_id: str, details: str, status: str = "ok"):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try: logs = json.load(f)
            except: logs = []
    logs.append({
        "time":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type":    event_type,
        "channel": channel_id,
        "details": details,
        "status":  status
    })
    # শুধু শেষ ৵৫০০ log রাখো
    if len(logs) > 500:
        logs = logs[-500:]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# ═════════════════════════════════════════════════════════════
# Core Agent Logic
# ═════════════════════════════════════════════════════════════

def run_channel_with_retry(channel_id: str, state: dict):
    """
    একটা channel এর pipeline চালায়।
    Error হলে MAX_RETRIES বার retry করে।
    """
    ch   = CHANNELS[channel_id]
    name = ch["name"]
    retries = 0

    while retries <= MAX_RETRIES:
        try:
            attempt_str = f"(চেষ্টা {retries+1}/{MAX_RETRIES+1})" if retries > 0 else ""
            print(f"\n{'='*55}")
            print(f"🤖 Agent → {name} {attempt_str}")
            print(f"⏰ সময়: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print(f"{'='*55}")

            # Pipeline চালাও (auto_upload=True)
            run_pipeline(channel_id=channel_id, auto_upload=True)

            # ✅ সফল হলে state update
            state["total_videos"] += 1
            state["channels"][channel_id]["videos_made"]          += 1
            state["channels"][channel_id]["last_run"]             = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            state["channels"][channel_id]["consecutive_errors"]   = 0
            state["channels"][channel_id]["last_error"]           = None
            save_state(state)

            log_event("video_created", channel_id,
                      f"Video #{state['channels'][channel_id]['videos_made']} তৈরি হয়েছে")

            notifier.send(
                f"✅ <b>[Agent] {name}</b>\n\n"
                f"🎬 Video #{state['channels'][channel_id]['videos_made']} সফলভাবে upload হয়েছে!\n"
                f"📊 মোট videos: {state['total_videos']}"
            )
            return True

        except Exception as e:
            retries += 1
            err_msg = str(e)[:300]
            print(f"\n❌ Error (চেষ্টা {retries}): {err_msg}")
            traceback.print_exc()

            state["total_errors"] += 1
            state["channels"][channel_id]["consecutive_errors"] += 1
            state["channels"][channel_id]["last_error"] = err_msg
            save_state(state)

            log_event("error", channel_id, err_msg, status="error")

            if retries <= MAX_RETRIES:
                wait = RETRY_DELAY * retries   # প্রতিবার বেশি অপেক্ষা
                print(f"⏳ {wait//60} মিনিট পরে আবার চেষ্টা করবে...")
                notifier.send(
                    f"⚠️ <b>[Agent] {name} — চেষ্টা {retries}/{MAX_RETRIES}</b>\n\n"
                    f"❌ Error: <code>{err_msg[:200]}</code>\n"
                    f"⏳ {wait//60} মিনিট পরে retry..."
                )
                time.sleep(wait)
            else:
                print(f"💀 {MAX_RETRIES} বার চেষ্টার পরেও হয়নি। আজকের জন্য skip।")
                notifier.send(
                    f"💀 <b>[Agent] {name} — সব চেষ্টা ব্যর্থ!</b>\n\n"
                    f"❌ <code>{err_msg[:200]}</code>\n\n"
                    f"⏭️ কাল আবার চেষ্টা হবে।"
                )
                return False

    return False


def run_all_channels(state: dict):
    """
    সব channel এর video বানায় (schedule অনুযায়ী)।
    """
    now_hour = datetime.datetime.now().hour

    for channel_id, ch in CHANNELS.items():
        try:
            upload_hour = int(ch.get("upload_time", "09:00").split(":")[0])
        except Exception:
            upload_hour = 9

        # আজকে এই channel এর জন্য ইতিমধ্যে video বানানো হয়েছে কিনা
        last_run = state["channels"][channel_id].get("last_run")
        if last_run:
            last_date = last_run.split(" ")[0]
            today     = datetime.date.today().strftime("%Y-%m-%d")
            if last_date == today:
                print(f"⏭️  {ch['name']} — আজকে ইতিমধ্যে done, skip।")
                continue

        # এই channel এর upload time হয়েছে কিনা
        if now_hour >= upload_hour:
            # একটু random delay যাতে YouTube spam না মনে করে
            delay = random.randint(0, 600)
            print(f"⏳ {ch['name']} শুরু হবে {delay//60}m {delay%60}s পরে...")
            time.sleep(delay)
            run_channel_with_retry(channel_id, state)
        else:
            remaining = upload_hour - now_hour
            print(f"⏰ {ch['name']} — আরও {remaining} ঘন্টা পরে শুরু হবে।")


# ═════════════════════════════════════════════════════════════
# Scheduler Jobs
# ═════════════════════════════════════════════════════════════

def daily_job():
    """প্রতিদিন এক বার চলে — সব channel চেক করে।"""
    print(f"\n🌅 Daily job শুরু: {datetime.datetime.now()}")
    state = load_state()
    run_all_channels(state)
    print(f"✅ Daily job শেষ: {datetime.datetime.now()}")


def health_check_job():
    """প্রতি ঘন্টায় চলে — agent জীবিত আছে জানায়।"""
    state = load_state()
    msgs  = []
    now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msgs.append(f"🤖 <b>Agent চলছে</b> — {now}")
    msgs.append(f"📊 মোট videos: {state['total_videos']}")
    msgs.append(f"❌ মোট errors: {state['total_errors']}")
    msgs.append("")

    for ch_id, ch_cfg in CHANNELS.items():
        ch_state = state["channels"].get(ch_id, {})
        last_run = ch_state.get("last_run", "কখনো না")
        count    = ch_state.get("videos_made", 0)
        errs     = ch_state.get("consecutive_errors", 0)
        status   = "✅" if errs == 0 else f"⚠️ ({errs} errors)"
        msgs.append(f"{status} <b>{ch_cfg['name']}</b>\n   Videos: {count} | Last: {last_run}")

    # Telegram তে silent notification
    notifier.send("\n".join(msgs), silent=True)


def hourly_check_job():
    """প্রতি ঘন্টায় চলে — কোনো missed channel আছে কিনা দেখে।"""
    state = load_state()
    now_hour = datetime.datetime.now().hour

    for channel_id, ch in CHANNELS.items():
        try:
            upload_hour = int(ch.get("upload_time", "09:00").split(":")[0])
        except Exception:
            upload_hour = 9

        # আজকের জন্য এখনো হয়নি এবং সময় পেরিয়ে গেছে
        last_run = state["channels"][channel_id].get("last_run")
        today    = datetime.date.today().strftime("%Y-%m-%d")

        already_done = last_run and last_run.split(" ")[0] == today
        time_passed  = now_hour >= upload_hour

        if not already_done and time_passed:
            print(f"🔔 Missed channel detected: {ch['name']} — এখনই চালাচ্ছি...")
            run_channel_with_retry(channel_id, state)


# ═════════════════════════════════════════════════════════════
# Main Agent Loop
# ═════════════════════════════════════════════════════════════

def start_agent():
    state = load_state()
    state["agent_started"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    save_state(state)

    print("\n" + "🤖"*20)
    print("   YouTube AI Agent চালু হচ্ছে...")
    print("   সম্পূর্ণ Autonomous — কোনো input লাগবে না")
    print("🤖"*20)

    # Channel schedule print করো
    print("\n📅 Channel Schedule:")
    for ch_id, ch in CHANNELS.items():
        print(f"   {ch['name']} → প্রতিদিন {ch.get('upload_time','09:00')}")

    # Telegram এ জানাও
    schedule_info = "\n".join([
        f"🕐 {ch['name']}: প্রতিদিন {ch.get('upload_time','09:00')}"
        for ch in CHANNELS.values()
    ])
    notifier.send(
        f"🤖 <b>YouTube AI Agent চালু হয়েছে!</b>\n\n"
        f"📅 <b>Schedule:</b>\n{schedule_info}\n\n"
        f"✅ সম্পূর্ণ Autonomous মোডে চলছে।"
    )

    # ── Schedule setup ────────────────────────────────────────
    # প্রতিদিন ভোর ৮টায় main job (hourly_check_job বাকিগুলো ধরবে)
    schedule.every().day.at("08:00").do(daily_job)

    # প্রতি ঘন্টায় missed channel চেক
    schedule.every().hour.do(hourly_check_job)

    # প্রতি ৬ ঘন্টায় health check
    schedule.every(6).hours.do(health_check_job)

    # Startup এ একবার চালাও (missed কিছু আছে কিনা দেখো)
    print("\n🔍 Startup check চলছে...")
    hourly_check_job()

    # ── Main loop ─────────────────────────────────────────────
    print("\n⏳ Agent loop শুরু — Ctrl+C দিয়ে বন্ধ করতে পারো\n")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)   # প্রতি ১ মিনিটে schedule চেক
        except KeyboardInterrupt:
            print("\n\n🛑 Agent বন্ধ করা হচ্ছে...")
            notifier.send("🛑 <b>Agent বন্ধ হয়েছে।</b>")
            break
        except Exception as e:
            print(f"⚠️ Agent loop error: {e}")
            log_event("agent_error", "system", str(e), status="warning")
            time.sleep(60)


# ═════════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube AI Agent")
    parser.add_argument("--now",     action="store_true", help="এখনই সব channel চালাও")
    parser.add_argument("--channel", type=str,            help="একটা নির্দিষ্ট channel চালাও")
    parser.add_argument("--status",  action="store_true", help="agent status দেখাও")
    args = parser.parse_args()

    if args.status:
        state = load_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.now:
        state = load_state()
        if args.channel:
            run_channel_with_retry(args.channel, state)
        else:
            for ch_id in CHANNELS:
                run_channel_with_retry(ch_id, state)

    else:
        start_agent()
