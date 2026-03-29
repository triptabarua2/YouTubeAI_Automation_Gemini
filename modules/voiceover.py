# modules/voiceover.py
# ElevenLabs দিয়ে বাংলা voiceover তৈরি করে

import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

OUTPUT_DIR = "temp/audio"

def generate_voiceover(text: str, filename: str) -> str:
    """
    Bengali text দিলে audio file বানায়।
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"  🎤 Voiceover তৈরি হচ্ছে: {filename}")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # বাংলা support করে
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.8,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"  ✅ Voiceover সেভ হয়েছে: {filepath}")
            return filepath
        else:
            print(f"  ⚠️ ElevenLabs error: {response.status_code} - {response.text}")
            return generate_silence(filename, 5)
    except Exception as e:
        print(f"  ⚠️ Voiceover error: {e}")
        return generate_silence(filename, 5)


def generate_silence(filename: str, duration: int = 5) -> str:
    """Fallback: নীরব audio তৈরি করে"""
    from pydub import AudioSegment
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    silence = AudioSegment.silent(duration=duration * 1000)
    silence.export(filepath, format="mp3")
    return filepath


def generate_all_voiceovers(scenes: list) -> list:
    """সব scene-এর voiceover একসাথে বানায়"""
    print(f"\n🎤 {len(scenes)}টি voiceover তৈরি হচ্ছে...")
    audio_paths = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        filename = f"voice_{scene_num:02d}.mp3"
        path = generate_voiceover(scene["narration"], filename)
        audio_paths.append(path)

    print(f"✅ সব voiceover তৈরি হয়েছে!")
    return audio_paths


def get_available_bengali_voices():
    """ElevenLabs-এ available বাংলা voices দেখায়"""
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        voices = response.json().get("voices", [])
        print("\n📢 Available Voices:")
        for v in voices[:10]:
            print(f"  - {v['name']}: {v['voice_id']}")
    except Exception as e:
        print(f"Error: {e}")
