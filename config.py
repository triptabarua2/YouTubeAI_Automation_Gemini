# ============================================================
#  config.py — সব API Key এবং ৩টি Channel Settings
# ============================================================

import os
from dotenv import load_dotenv

# .env ফাইল থেকে environment variables লোড করা
load_dotenv()

# ✅ Colab Secrets সাপোর্ট (যদি Colab-এ রান করা হয়)
try:
    from google.colab import userdata
    COLAB_AVAILABLE = True
except ImportError:
    COLAB_AVAILABLE = False

def get_secret(key, default=None):
    """Colab Secrets অথবা Environment Variables থেকে ডেটা আনে।"""
    if COLAB_AVAILABLE:
        try:
            return userdata.get(key)
        except:
            pass
    return os.getenv(key, default)

# ✅ API Keys লোড করা
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = get_secret("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY     = get_secret("GOOGLE_API_KEY")
GROQ_API_KEY       = get_secret("GROQ_API_KEY")
ELEVENLABS_API_KEY = get_secret("ELEVENLABS_API_KEY")

# ✅ Dummy environment setup for Colab/Linux errors
if COLAB_AVAILABLE or os.name != 'nt':
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-root"
    os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

# ✅ ElevenLabs — voiceover (মাসে ১০,০০০ chars ফ্রি)
ELEVENLABS_VOICE_ID_BN = get_secret("ELEVENLABS_VOICE_ID_BN", "YOUR_BENGALI_VOICE_ID")
ELEVENLABS_VOICE_ID_EN = get_secret("ELEVENLABS_VOICE_ID_EN", "YOUR_ENGLISH_VOICE_ID")
ELEVENLABS_VOICE_ID_HI = get_secret("ELEVENLABS_VOICE_ID_HI", "DpnM70iDHNHZ0Mguv6GJ")
ELEVENLABS_VOICE_ID    = ELEVENLABS_VOICE_ID_HI  # Set Hindi as default since BN is unavailable

# ✅ Google Cloud TTS — ElevenLabs শেষ হলে fallback (মাসে ১০ লাখ chars ফ্রি)
GOOGLE_CLOUD_TTS_API_KEY = get_secret("GOOGLE_CLOUD_TTS_API_KEY")

# ✅ Pixabay — background music (ফ্রি)
PIXABAY_API_KEY = get_secret("PIXABAY_API_KEY")

# ✅ YouTube client secret — ৩টা channel-এর জন্য আলাদা file
# console.cloud.google.com থেকে প্রতিটা channel-এর OAuth credentials ডাউনলোড করুন
# ============================================================

# ============================================================
#  ৩টি Channel-এর Settings
# ============================================================
CHANNELS = {

    "channel_1": {
        "name":              "আমার বাংলা চ্যানেল ১",          # channel-এর নাম
        "topic":             "funny",                          # channel-এর বিষয়
        "topic_description": "বাংলাদেশের মজার ও হাসির ঘটনা, viral memes, comedy animation",
        "style":             "funny, relatable, Bangladeshi humor",
        "upload_time":       "09:00",                         # সকাল ৯টায়
        "client_secret":     "client_secret_channel1.json",   # YouTube OAuth file
        "token_file":        "token_channel1.pickle",
        "category_id":       "23",                            # 23 = Comedy
        "language":          "bn",
    },

    "channel_2": {
        "name":              "আমার বাংলা চ্যানেল ২",
        "topic":             "educational",
        "topic_description": "বাংলাদেশ ও বিশ্বের অজানা তথ্য, ইতিহাস, বিজ্ঞান, শিক্ষামূলক animation",
        "style":             "educational, informative, engaging, suitable for all ages",
        "upload_time":       "13:00",                         # দুপুর ১টায়
        "client_secret":     "client_secret_channel2.json",
        "token_file":        "token_channel2.pickle",
        "category_id":       "27",                            # 27 = Education
        "language":          "bn",
    },

    "channel_3": {
        "name":              "আমার বাংলা চ্যানেল ৩",
        "topic":             "storytelling",
        "topic_description": "বাংলাদেশের রহস্য, ভূতের গল্প, রোমাঞ্চকর কাহিনী, mystery animation",
        "style":             "mysterious, thrilling, dramatic, suspenseful",
        "upload_time":       "20:00",                         # রাত ৮টায়
        "client_secret":     "client_secret_channel3.json",
        "token_file":        "token_channel3.pickle",
        "category_id":       "24",                            # 24 = Entertainment
        "language":          "bn",
    },

}

# ============================================================
#  Global Video Settings (সব channel-এ একই)
# ============================================================
SCENES_PER_VIDEO       = 8
FPS                    = 24
RESOLUTION             = (1920, 1080)
VIDEO_DURATION_SECONDS = 180
# Font Path
FONT_PATH = os.path.join("assets", "Kalpurush.ttf")
