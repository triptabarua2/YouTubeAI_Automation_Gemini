# modules/script_generator.py
# Google Gemini দিয়ে channel-এর topic অনুযায়ী script তৈরি করে
# ✅ Updated: google.generativeai → google.genai (নতুন package)

from google import genai
import json, sys, os, datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, SCENES_PER_VIDEO

# নতুন model name (gemini-2.0-flash)
MODEL = "gemini-2.0-flash"


def generate_script(topic: str, channel_style: str = "", topic_type: str = "funny") -> dict:
    print(f"📝 Script তৈরি হচ্ছে: '{topic}' [{topic_type}]")

    client = genai.Client(api_key=GOOGLE_API_KEY)

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
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
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
        return {"title": topic, "scenes": []}


def get_trending_topic(topic_type: str = "funny", topic_description: str = "") -> str:
    client = genai.Client(api_key=GOOGLE_API_KEY)

    date = datetime.date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {date}.
Find ONE viral/trending topic in Bangladesh for a {topic_type} Bengali animation channel.
Channel focus: {topic_description}

Return ONLY the topic in Bengali with a relevant emoji. No explanation.
Example: "বিদ্যুৎ বিল দেখে মধ্যবিত্তের হার্ট অ্যাটাক 😂"
"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        topic = response.text.strip()
        print(f"💡 Trending Topic [{topic_type}]: {topic}")
        return topic
    except Exception as e:
        print(f"⚠️ Topic fetch error: {e}")
        return f"বাংলাদেশের আজকের সেরা মুহূর্ত 🔥"
