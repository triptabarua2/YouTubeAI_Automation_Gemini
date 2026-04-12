# modules/image_generator.py
# Pollinations.ai FREE AI animation images — কোনো API key লাগে না!

import requests, os, time
from PIL import Image
from io import BytesIO

DEFAULT_OUTPUT_DIR = "temp/images"

# Topic-specific animation style prompts
STYLE = {
    "funny": (
        "2D flat cartoon animation style, bright vibrant colors, bold outlines, "
        "Bangladeshi character, comic style, expressive faces, cheerful, "
        "clean lines, professional illustration, no text, no watermark"
    ),
    "educational": (
        "2D educational animation, infographic style, modern clean design, "
        "blue and white palette, clear visual storytelling, simple cartoon, "
        "bright colors, professional, no text, no watermark"
    ),
    "storytelling": (
        "2D animated scene, dramatic atmospheric lighting, cinematic composition, "
        "rich dark colors with accent lighting, mystery thriller animation style, "
        "detailed background, emotional, no text, no watermark"
    ),
}
DEFAULT_STYLE = "2D flat animation cartoon style, vibrant colors, clean lines, professional illustration, no text"


def generate_image(prompt: str, filename: str,
                   width: int = 1920, height: int = 1080,
                   output_dir: str = None, topic: str = "funny") -> str:
    out = output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(out, exist_ok=True)
    filepath = os.path.join(out, filename)

    style = STYLE.get(topic, DEFAULT_STYLE)
    full  = f"{prompt}, {style}"
    enc   = full.replace(" ", "%20").replace(",", "%2C").replace("(", "%28").replace(")", "%29")
    url   = f"https://image.pollinations.ai/prompt/{enc}?width={width}&height={height}&nologo=true&model=flux"

    print(f"  🎨 Generating: {filename}")
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                img.save(filepath, "PNG")
                print(f"  ✅ Saved: {filepath}")
                time.sleep(2.5)
                return filepath
            print(f"  ⚠ HTTP {r.status_code} (attempt {attempt+1})")
        except Exception as e:
            print(f"  ⚠ Attempt {attempt+1}: {e}")
            time.sleep(5 + attempt * 3)

    # Fallback gradient
    print(f"  🎨 Gradient fallback: {filename}")
    FALLBACK = {
        "funny":         [(30,15,80),(80,15,120)],
        "educational":   [(10,40,90),(10,80,60)],
        "storytelling":  [(30,5,60),(60,5,90)],
    }
    c = FALLBACK.get(topic, [(20,20,60),(50,15,80)])
    arr = Image.new("RGB",(width,height))
    pixels = arr.load()
    for y in range(height):
        t = y/height
        for x in range(width):
            pixels[x,y] = (
                int(c[0][0]*(1-t)+c[1][0]*t),
                int(c[0][1]*(1-t)+c[1][1]*t),
                int(c[0][2]*(1-t)+c[1][2]*t),
            )
    arr.save(filepath,"PNG")
    return filepath


def generate_thumbnail(prompt: str, title: str,
                        temp_dir: str = None, topic: str = "funny") -> str:
    out = os.path.join(temp_dir,"images") if temp_dir else DEFAULT_OUTPUT_DIR
    return generate_image(
        f"{prompt}, YouTube thumbnail, bold eye-catching, dramatic",
        "thumbnail.png", 1280, 720, output_dir=out, topic=topic
    )


def generate_all_scene_images(scenes: list, temp_dir: str = None,
                               topic: str = "funny") -> list:
    out = os.path.join(temp_dir,"images") if temp_dir else DEFAULT_OUTPUT_DIR
    print(f"\n🎨 {len(scenes)}টি animation scene image তৈরি হচ্ছে ({topic} style)...")
    paths = []
    for scene in scenes:
        n    = scene["scene_number"]
        path = generate_image(scene["image_prompt"], f"scene_{n:02d}.png",
                               output_dir=out, topic=topic)
        paths.append(path)
    print("✅ সব image তৈরি!")
    return paths
