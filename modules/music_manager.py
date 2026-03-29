# modules/music_manager.py
# Pixabay Free Music API দিয়ে automatic background music ডাউনলোড করে
# Pixabay API Key সম্পূর্ণ ফ্রি: https://pixabay.com/api/docs/

import os
import sys
import requests
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PIXABAY_API_KEY

MUSIC_DIR = "music"
CACHE_FILE = "music/downloaded.txt"

# ভিডিওর mood অনুযায়ী music category
MOOD_MAP = {
    "educational":  ["calm", "ambient", "corporate"],
    "storytelling": ["cinematic", "dramatic", "ambient"],
    "funny":        ["happy", "upbeat", "fun"],
    "adventure":    ["epic", "cinematic", "upbeat"],
    "mystery":      ["dark", "cinematic", "dramatic"],
    "default":      ["ambient", "calm", "corporate"],
}


def detect_mood(script_data: dict) -> str:
    """Script দেখে video-র mood বোঝে"""
    title = script_data.get("title", "").lower()
    tags  = " ".join(script_data.get("tags", [])).lower()
    text  = title + " " + tags

    if any(w in text for w in ["রহস্য", "mystery", "dark", "ভূত", "horror"]):
        return "mystery"
    if any(w in text for w in ["মজা", "funny", "comedy", "হাসি"]):
        return "funny"
    if any(w in text for w in ["adventure", "যাত্রা", "অ্যাডভেঞ্চার"]):
        return "adventure"
    if any(w in text for w in ["গল্প", "story", "ইতিহাস", "history"]):
        return "storytelling"
    return "educational"


def download_music(mood: str = "default") -> str | None:
    """
    Pixabay থেকে mood অনুযায়ী music ডাউনলোড করে।
    Returns: local file path অথবা None
    """
    os.makedirs(MUSIC_DIR, exist_ok=True)

    if not PIXABAY_API_KEY or PIXABAY_API_KEY == "YOUR_PIXABAY_API_KEY":
        print("  ⚠️  Pixabay API Key নেই — local music ব্যবহার হবে")
        return _get_local_music()

    categories = MOOD_MAP.get(mood, MOOD_MAP["default"])
    random.shuffle(categories)

    for category in categories:
        try:
            print(f"  🎵 Music খোঁজা হচ্ছে: mood={mood}, category={category}")
            url = (
                f"https://pixabay.com/api/music/"
                f"?key={PIXABAY_API_KEY}"
                f"&category={category}"
                f"&per_page=10"
            )
            resp = requests.get(url, timeout=15)
            data = resp.json()
            hits = data.get("hits", [])

            if not hits:
                continue

            # ডাউনলোড হয়নি এমন একটি বাছা
            already = _get_downloaded_list()
            new_hits = [h for h in hits if str(h["id"]) not in already]
            chosen = random.choice(new_hits if new_hits else hits)

            music_url  = chosen["audio"]
            music_id   = str(chosen["id"])
            music_name = f"music_{mood}_{music_id}.mp3"
            music_path = os.path.join(MUSIC_DIR, music_name)

            if os.path.exists(music_path):
                print(f"  ✅ Cached music: {music_path}")
                return music_path

            print(f"  ⬇️  Downloading: {chosen.get('tags', 'music')} ({chosen.get('duration', '?')}s)")
            audio_resp = requests.get(music_url, timeout=60)
            with open(music_path, "wb") as f:
                f.write(audio_resp.content)

            _add_to_downloaded(music_id)
            print(f"  ✅ Music সেভ হয়েছে: {music_path}")
            return music_path

        except Exception as e:
            print(f"  ⚠️  Music download error ({category}): {e}")
            continue

    return _get_local_music()


def _get_local_music() -> str | None:
    """music/ folder-এ আগে থেকে থাকা files থেকে বাছে"""
    if not os.path.exists(MUSIC_DIR):
        return None
    files = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.endswith((".mp3", ".wav", ".ogg"))
    ]
    return random.choice(files) if files else None


def _get_downloaded_list() -> list:
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE) as f:
        return f.read().splitlines()


def _add_to_downloaded(music_id: str):
    with open(CACHE_FILE, "a") as f:
        f.write(music_id + "\n")


def get_music_for_video(script_data: dict) -> str | None:
    """
    Script দেখে mood বুঝে, সেই অনুযায়ী music এনে দেয়।
    main.py এ শুধু এটাই call করতে হবে।
    """
    mood = detect_mood(script_data)
    print(f"\n🎵 Video mood: {mood} — সেই অনুযায়ী music আনা হচ্ছে...")
    path = download_music(mood)
    if path:
        print(f"  🎶 Music ready: {path}")
    else:
        print("  ⚠️  কোনো music পাওয়া যায়নি, music ছাড়াই চলবে")
    return path
