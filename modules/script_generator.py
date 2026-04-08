# modules/script_generator.py
# Google Gemini দিয়ে channel-এর topic অনুযায়ী script তৈরি করে

import google.generativeai as genai
import json, sys, os, datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, SCENES_PER_VIDEO


def generate_script(topic: str, channel_style: str = "", topic_type: str = "funny") -> dict:
    print(f"📝 Script তৈরি হচ্ছে: '{topic}' [{topic_type}]")

    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Try multiple model names for compatibility
    model_names = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
    model = None
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # Test if model is available by doing a very small generation if needed, 
            # but usually just initializing is fine. We'll try to generate below.
            break
        except Exception:
            continue
            
    if not model:
        print("❌ No compatible Gemini model found.")
        return {"title": topic, "scenes": []}

    style_instructions = {
        "funny": "Use Bengali slang, jokes, puns, exaggerated humor. Tone: like a funny friend telling a story.",
        "educational": "Use clear facts, interesting trivia, easy explanations. Tone: friendly teacher.",
        "storytelling": "Use suspense, dramatic pauses, mystery. Tone: thrilling narrator.",
    }
    style_note = style_instructions.get(topic_type, style_instructions["funny"])

    prompt = f"""You are a Bengali YouTube animator creating a {topic_type} animated video.

Topic: "{topic}"
Channel Style: {channel_style}
Style Note: {style_note}

For each scene provide narration in THREE languages: Bengali, Hindi, English.

Return ONLY valid JSON:
{{
  "title": "Clickbait Bengali title with emoji",
  "description": "Bengali description (150 words) with emoji",
  "tags": ["tag1", "tag2", "animation", "bengali", "বাংলা"],
  "mood": "{topic_type}",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 20,
      "narration": "Bengali narration",
      "translation_hindi": "Hindi translation",
      "translation_english": "English translation",
      "joke": "Funny/interesting one-liner in Bengali",
      "character_emotion": "shocked / laughing / facepalm / jumping / confused / proud / scared / crying_laugh",
      "visual_description": "Scene description in English",
      "image_prompt": "2D animation scene, cartoon style, bright colors"
    }}
  ],
  "thumbnail_prompt": "Eye-catching thumbnail, 2D animation style",
  "hook": "First line that grabs attention in 3 seconds"
}}

Make exactly {SCENES_PER_VIDEO} scenes.
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        print(f"✅ Script তৈরি: {len(data['scenes'])} scenes [{topic_type}]")
        return data
    except Exception as e:
        print(f"❌ Script generation error: {e}")
        # Fallback empty structure
        return {"title": topic, "scenes": []}


def get_trending_topic(topic_type: str = "funny", topic_description: str = "") -> str:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    model_names = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
    model = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            break
        except Exception:
            continue
            
    if not model:
        return f"বাংলাদেশের আজকের সেরা মুহূর্ত 🔥"

    date  = datetime.date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {date}.
Find ONE viral/trending topic in Bangladesh for a {topic_type} Bengali animation channel.
Channel focus: {topic_description}

Return ONLY the topic in Bengali with a relevant emoji. No explanation.
Example: "বিদ্যুৎ বিল দেখে মধ্যবিত্তের হার্ট অ্যাটাক 😂"
"""
    try:
        resp  = model.generate_content(prompt)
        topic = resp.text.strip()
        print(f"💡 Trending Topic [{topic_type}]: {topic}")
        return topic
    except Exception as e:
        print(f"⚠️ Topic fetch error: {e}")
        return f"বাংলাদেশের আজকের সেরা মুহূর্ত 🔥"
