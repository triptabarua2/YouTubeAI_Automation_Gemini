# 🎬 YouTube AI Animation — সম্পূর্ণ সেটআপ গাইড

## এই system কী করে?

```
🤖 AI Topic বাছাই (Groq/Llama)
   ↓
📝 Script লেখা (৮টি scene, Bengali/Hindi/English)
   ↓
🎨 AI Animation Images (Pollinations.ai — FREE, no key!)
   ↓
🎤 Voiceover (ElevenLabs বা gTTS fallback)
   ↓
🎬 Animation Video তৈরি:
   • Animated intro title card
   • Ken Burns background effects
   • Emotion-based character animations
   • Speech bubbles (funny channel)
   • Typewriter subtitles
   • Floating particles
   • Flash transitions between scenes
   • Subscribe/outro animation
   ↓
📤 YouTube Auto-Upload (Private, তুমি Public করবে)
   ↓
📱 Telegram Notification
```

---

## ⚡ Quick Start (সবচেয়ে সহজ পথ)

### ধাপ ১ — Requirements install
```bash
pip install -r requirements.txt
```

### ধাপ ২ — API Keys সেটআপ
```bash
cp .env.example .env
# .env ফাইল খোলো এবং keys বসাও
```

### ধাপ ৩ — Run!
```bash
# Test করো (YouTube upload ছাড়া)
python demo_runner.py

# একটি channel চালাও
python main.py --channel channel_1 --auto-upload

# সব channel একসাথে
python main.py --all --auto-upload

# প্রতিদিন schedule
python main.py --schedule
```

---

## 🔑 API Keys — কোথায় পাবে

### 1. Groq API Key (Script — সম্পূর্ণ ফ্রি)
1. যাও: https://console.groq.com
2. Sign up → API Keys → Create
3. `.env`-এ `GROQ_API_KEY=` এখানে বসাও

### 2. ElevenLabs (Voice — মাসে 10,000 chars ফ্রি)
1. যাও: https://elevenlabs.io → Sign up
2. Profile → API Key কপি করো
3. Voice Library → বাংলা voice বেছে Voice ID কপি করো
4. `.env`-এ বসাও

   **💡 Tip:** ElevenLabs না থাকলেও চলবে — gTTS (Google Text-to-Speech) দিয়ে fallback হবে! সম্পূর্ণ ফ্রি।

### 3. YouTube API (Upload — সবচেয়ে গুরুত্বপূর্ণ)
1. যাও: https://console.cloud.google.com
2. নতুন Project বানাও
3. "APIs & Services" → "Enable APIs" → "YouTube Data API v3" Enable করো
4. "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: **Desktop app**
6. JSON download করো → নাম দাও `client_secret_channel1.json`
7. প্রজেক্ট ফোল্ডারে রাখো
8. **প্রথমবার run করলে browser খুলবে** → YouTube account দিয়ে login করো

---

## 📁 ফাইল স্ট্রাকচার

```
YouTubeAI_Animation/
├── .env                          ← তোমার API keys (গোপন রাখো!)
├── .env.example                  ← template
├── config.py                     ← channel settings
├── main.py                       ← main pipeline
├── demo_runner.py                ← upload ছাড়া test
├── requirements.txt
├── assets/
│   ├── character.png             ← তোমার character (পরিবর্তন করো!)
│   └── Kalpurush.ttf            ← বাংলা font
├── modules/
│   ├── animation_effects.py     ← 🆕 সব animation effects
│   ├── video_editor.py          ← 🆕 Animation video pipeline
│   ├── image_generator.py       ← 🆕 Better AI image prompts
│   ├── script_generator.py      ← Groq দিয়ে script
│   ├── voiceover.py             ← ElevenLabs/gTTS voice
│   ├── youtube_uploader.py      ← YouTube upload
│   ├── music_manager.py         ← Background music
│   └── notifier.py              ← Telegram notification
├── output/                       ← তৈরি videos এখানে
└── video_log.json               ← upload history
```

---

## 🎭 Animation Features (নতুন!)

| Feature | বিবরণ |
|---------|--------|
| 🎬 Animated Intro | Title zoom-in with bounce + particles |
| 🌅 Ken Burns Effect | Background zoom/pan animations |
| 👤 Character Emotions | shocked/laughing/jumping/scared/etc |
| 💬 Speech Bubbles | Animated bubble (funny channel) |
| ✍️ Typewriter Subtitles | Bengali text types itself |
| ✨ Floating Particles | Topic-colored sparkles |
| ⚡ Flash Transitions | Between each scene |
| 📱 Subscribe Outro | Animated subscribe button |

---

## 🎨 Character পরিবর্তন করতে

`assets/character.png` ফাইলটা replace করো।
- যেকোনো cartoon character PNG
- White বা transparent background
- Tall portrait orientation (3:4 ratio ভালো)

---

## ⚠️ সমস্যা হলে

- `video_log.json` — error history
- `output/` — তৈরি videos
- ElevenLabs কাজ না করলে → gTTS automatically use হবে
- Image তৈরি না হলে → gradient placeholder use হবে
- YouTube upload এ error → `token_channel1.pickle` ডিলিট করে আবার run করো
