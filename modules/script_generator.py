# modules/script_generator.py
# Google Gemini API দিয়ে FUNNY script তৈরি করে

import google.generativeai as genai
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, SCENES_PER_VIDEO

def generate_script(topic: str) -> dict:
    print(f"📝 Funny Script তৈরি হচ্ছে: '{topic}'")

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""You are a FUNNY Bengali YouTube animator — think cartoon show meets comedy roast.

Create a HILARIOUS animated video script for: "{topic}"

Rules for FUNNY content:
- Use Bengali slang and everyday expressions (ভাই, আরে বাবা, কী আজব, মাথা নষ্ট etc.)
- Add JOKES, PUNS, and funny comparisons in narration
- Each scene should have ONE funny moment (surprise, exaggeration, or absurdity)
- Character reacts expressively: shocked, laughing, facepalming, jumping for joy
- Use relatable Bangladeshi humor — rickshaw, bazar, dada-nana, school, etc.
- Narration tone: like a funny friend telling a story, NOT a news anchor

Return ONLY valid JSON, no extra text:
{{
  "title": "Funny clickbait Bengali title with emoji",
  "description": "Funny Bengali description (150 words) with emoji",
  "tags": ["funny", "animation", "bengali", "comedy", "হাসির ভিডিও", "মজার", "বাংলা", "cartoon", "animated", "bangladesh", "comedy animation", "funny bengali", "বাংলা কার্টুন", "হাসি", "মজা"],
  "mood": "funny",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 20,
      "narration": "Funny Bengali narration with jokes and exaggeration",
      "joke": "The specific joke or punchline in this scene (1 short line in Bengali)",
      "character_emotion": "one of: shocked / laughing / facepalm / jumping / confused / proud / scared / crying_laugh",
      "visual_description": "Funny visual scene in English",
      "image_prompt": "Funny 2D animation scene, cartoon style, exaggerated, bright colors, comedic"
    }}
  ],
  "thumbnail_prompt": "Funny thumbnail — character shocked/laughing face, bold colors, comedic, 2D animation",
  "hook": "First funny line that makes viewer laugh in 3 seconds"
}}

Make exactly {SCENES_PER_VIDEO} scenes. Keep it SHORT, PUNCHY, and FUNNY.
"""

    response = model.generate_content(prompt)
    response_text = response.text.strip()

    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    script_data = json.loads(response_text)
    print(f"✅ Funny Script তৈরি: {len(script_data['scenes'])} scenes")
    return script_data


def get_trending_topic() -> str:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    response = model.generate_content(
        """Suggest ONE funny YouTube video topic for a Bengali comedy animation channel.
Relatable to Bangladeshi life, comedic everyday situations.
Example: "বাংলাদেশি মায়েরা যখন বলেন 'একটু পরে খাবো' 😂"
Return ONLY the topic in Bengali with emoji, nothing else."""
    )
    topic = response.text.strip()
    print(f"💡 Auto funny topic: {topic}")
    return topic
