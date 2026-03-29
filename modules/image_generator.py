# modules/image_generator.py
# Pollinations.ai দিয়ে FREE AI image তৈরি করে (কোনো API key লাগে না!)

import requests
import os
import time
from PIL import Image
from io import BytesIO

OUTPUT_DIR = "temp/images"

def generate_image(prompt: str, filename: str, width: int = 1920, height: int = 1080) -> str:
    """
    Text prompt দিলে AI image বানিয়ে save করে।
    Pollinations.ai — সম্পূর্ণ ফ্রি, কোনো API key লাগে না।
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    # 2D animation style যোগ করা
    full_prompt = f"{prompt}, 2D flat animation style, vibrant colors, clean lines, cartoon, professional illustration, no text"
    full_prompt = full_prompt.replace(" ", "%20")

    url = f"https://image.pollinations.ai/prompt/{full_prompt}?width={width}&height={height}&nologo=true"

    print(f"  🎨 Image তৈরি হচ্ছে: {filename}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img.save(filepath, "PNG")
                print(f"  ✅ Image সেভ হয়েছে: {filepath}")
                time.sleep(2)  # Rate limiting
                return filepath
        except Exception as e:
            print(f"  ⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(5)

    # Fallback: solid color image
    print(f"  ⚠️ Image generation failed, using fallback")
    img = Image.new('RGB', (width, height), color=(26, 26, 46))
    img.save(filepath, "PNG")
    return filepath


def generate_thumbnail(prompt: str, title: str) -> str:
    """Thumbnail image বানায়"""
    thumb_prompt = f"{prompt}, YouTube thumbnail, bold composition, eye-catching, 2D animation style"
    return generate_image(thumb_prompt, "thumbnail.png", width=1280, height=720)


def generate_all_scene_images(scenes: list) -> list:
    """সব scene-এর image একসাথে বানায়"""
    print(f"\n🎨 {len(scenes)}টি scene image তৈরি হচ্ছে...")
    image_paths = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        filename = f"scene_{scene_num:02d}.png"
        path = generate_image(scene["image_prompt"], filename)
        image_paths.append(path)

    print(f"✅ সব image তৈরি হয়েছে!")
    return image_paths
