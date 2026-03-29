# modules/script_generator.py
# Google Gemini API দিয়ে script তৈরি করে

import google.generativeai as genai
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, CHANNEL_STYLE, SCENES_PER_VIDEO

def generate_script(topic: str) -> dict:
    """
    Topic দিলে পুরো video script JSON আকারে return করে।
    """
    print(f"📝 Script তৈরি হচ্ছে: '{topic}'")

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""You are a YouTube script writer for a Bengali 2D animation channel.

Create a complete video script for the topic: "{topic}"

Style: {CHANNEL_STYLE}

Return ONLY a valid JSON object with this exact structure (no extra text):
{{
  "title": "YouTube-friendly Bengali title (clickbait but honest)",
  "description": "YouTube description in Bengali (150 words, include keywords)",
  "tags": ["tag1", "tag2", "tag3", ...15 tags total],
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 20,
      "narration": "Exact Bengali text to be spoken by voice actor",
      "visual_description": "Describe what to show visually in English (for image generation)",
      "image_prompt": "Detailed prompt for AI image generation, 2D animation style, flat design, colorful"
    }}
  ],
  "thumbnail_prompt": "Detailed image prompt for thumbnail, 2D animation style, bold colors, Bengali text space",
  "hook": "First sentence - must grab attention in 3 seconds"
}}

Make exactly {SCENES_PER_VIDEO} scenes. Total narration should be ~3 minutes when read aloud.
Keep narration natural Bengali - like talking to a friend, not formal.
"""

    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # JSON parse করা
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    try:
        script_data = json.loads(response_text)
        print(f"✅ Script তৈরি হয়েছে: {len(script_data['scenes'])} scenes")
        return script_data
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw response: {response_text}")
        raise e


def get_trending_topic() -> str:
    """
    Gemini দিয়ে trending/interesting topic suggest করায়
    """
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = """Suggest ONE interesting YouTube video topic for a Bengali 2D animation channel.
Topic should be: educational or storytelling, interesting for Bangladeshi audience, trending or evergreen.
Return ONLY the topic in Bengali, nothing else. Example: "পৃথিবীর সবচেয়ে রহস্যময় জায়গাগুলো" """

    response = model.generate_content(prompt)
    topic = response.text.strip()
    print(f"💡 Auto topic: {topic}")
    return topic
