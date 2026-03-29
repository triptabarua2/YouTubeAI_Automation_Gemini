# 🎬 YouTube AI Full Automation — সেটআপ গাইড

## এই system কী করবে?
```
আপনি কিছু না করলেও প্রতিদিন:
Topic বাছাই → Script লেখা → AI Image বানানো → 
Voiceover দেওয়া → Video Edit → YouTube Upload
```

---

## ধাপ ১ — Python ইনস্টল করুন
👉 https://python.org/downloads (3.10 বা উপরে)

---

## ধাপ ২ — Libraries ইনস্টল করুন
```bash
pip install -r requirements.txt
```

---

## ধাপ ৩ — API Keys সংগ্রহ করুন

### A) Anthropic API Key (Claude — Script লেখার জন্য)
1. https://console.anthropic.com যান
2. Sign Up করুন (Google দিয়ে)
3. Billing → Add Payment Method
4. API Keys → "Create Key" → Copy করুন
5. `config.py` তে `ANTHROPIC_API_KEY = "..."` এখানে বসান

### B) ElevenLabs API Key (Voiceover — বাংলা voice)
1. https://elevenlabs.io যান
2. Free Sign Up করুন
3. Profile → API Key → Copy করুন
4. Voices → বাংলা voice বাছুন → Voice ID copy করুন
5. `config.py` তে দুটোই বসান

**বাংলা Voice খুঁজে পেতে:**
```bash
python -c "from modules.voiceover import get_available_bengali_voices; get_available_bengali_voices()"
```

### C) YouTube API (Upload করার জন্য)
1. https://console.cloud.google.com যান
2. New Project বানান: "YouTubeAI"
3. APIs & Services → Enable → "YouTube Data API v3"
4. Credentials → OAuth 2.0 Client ID → Desktop App
5. JSON ডাউনলোড করুন → rename করুন `client_secret.json`
6. এই folder-এ রাখুন

---

## ধাপ ৪ — Music যোগ করুন (Optional)
`music/` folder-এ যেকোনো royalty-free .mp3 রাখুন।
ফ্রি music পাবেন: https://pixabay.com/music

---

## ধাপ ৫ — Run করুন!

### একটি video বানানো (topic নিজে দিয়ে):
```bash
python main.py --topic "বাংলাদেশের সেরা ১০টি রহস্য"
```

### AI নিজে topic বাছুক:
```bash
python main.py
```

### Video বানিয়ে সাথে সাথে upload করা:
```bash
python main.py --auto-upload
```

### প্রতিদিন automatic (schedule mode):
```bash
python main.py --schedule
```
> এটা চালিয়ে রাখলে `config.py` তে দেওয়া সময়ে প্রতিদিন video বানিয়ে upload করবে!

### পুরনো video-র list দেখতে:
```bash
python main.py --logs
```

---

## কতটুকু ফ্রি, কতটুকু টাকা লাগবে?

| Service | ফ্রি কোটা | মাসে খরচ |
|---------|-----------|----------|
| Anthropic | প্রথম $5 ফ্রি | ~৳500-800 |
| ElevenLabs | 10,000 chars/মাস ফ্রি | ফ্রিতেই চলবে |
| Pollinations.ai (Image) | সম্পূর্ণ ফ্রি ✅ | ৳0 |
| YouTube API | সম্পূর্ণ ফ্রি ✅ | ৳0 |

---

## সমস্যা হলে
- `video_log.json` দেখুন — কী হয়েছে record আছে
- `output/script.json` দেখুন — script ঠিক হয়েছে কিনা
- API key ভুল থাকলে error message আসবে
