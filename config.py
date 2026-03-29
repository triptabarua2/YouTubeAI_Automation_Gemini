# ============================================================
#  config.py — এখানে আপনার সব API Key বসান
# ============================================================

# ✅ Telegram Bot — মোবাইলে notification পাওয়ার জন্য (সম্পূর্ণ ফ্রি)
# Bot বানাতে: Telegram-এ @BotFather খুঁজুন → /newbot → token copy করুন
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
# Chat ID পেতে: @userinfobot-এ /start দিন → আপনার ID copy করুন
TELEGRAM_CHAT_ID   = "YOUR_TELEGRAM_CHAT_ID"

# ✅ Google Gemini (Free) — script লেখার জন্য
# পাবেন: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = "AIzaSyBJoG6NHpXnATaXiGEoO-XpMZ8yLHzSUqA"

# ✅ ElevenLabs — বাংলা voiceover এর জন্য
# পাবেন: https://elevenlabs.io (ফ্রি signup)
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY"
ELEVENLABS_VOICE_ID = "YOUR_VOICE_ID"  # ElevenLabs dashboard থেকে বাংলা voice বাছুন

# ✅ Pixabay — automatic background music ডাউনলোড (সম্পূর্ণ ফ্রি)
# পাবেন: https://pixabay.com/api/docs/ → "Get API Key" (ফ্রি signup)
PIXABAY_API_KEY = "YOUR_PIXABAY_API_KEY"

# ✅ YouTube — upload এর জন্য
# পাবেন: https://console.cloud.google.com
# (নিচে SETUP_GUIDE.md তে বিস্তারিত আছে)
YOUTUBE_CLIENT_SECRET_FILE = "client_secret.json"

# ============================================================
#  Channel Settings
# ============================================================
CHANNEL_LANGUAGE = "bn"          # বাংলা
CHANNEL_TOPIC = "2D animation educational and storytelling videos in Bengali"
CHANNEL_STYLE = "engaging, fun, educational, suitable for Bangladeshi audience"
VIDEO_CATEGORY_ID = "27"         # Education

# ============================================================
#  Video Settings
# ============================================================
VIDEO_DURATION_SECONDS = 180     # ~৩ মিনিটের ভিডিও
SCENES_PER_VIDEO = 8             # কতটি scene থাকবে
FPS = 24
RESOLUTION = (1920, 1080)        # Full HD

# ============================================================
#  Schedule — কখন ভিডিও upload হবে
# ============================================================
UPLOAD_TIME = "10:00"            # সকাল ১০টায়
UPLOAD_DAYS = ["monday", "wednesday", "friday"]  # সপ্তাহে ৩ দিন
