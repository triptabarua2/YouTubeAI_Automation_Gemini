import os
import json
import sys
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.script_generator import generate_script
from modules.video_editor import create_video
from config import RESOLUTION, FPS

def create_dummy_background(text, filename):
    """Creates a simple background image for the demo."""
    # Create a nice gradient background
    img = Image.new('RGB', RESOLUTION, color=(30, 30, 50))
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes to make it look like a background
    for i in range(10):
        x = np.random.randint(0, RESOLUTION[0])
        y = np.random.randint(0, RESOLUTION[1])
        r = np.random.randint(50, 200)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(40, 40, 70))
        
    draw.text((RESOLUTION[0]//2, RESOLUTION[1]//2), text, fill=(200, 200, 200), anchor="mm")
    img.save(filename)
    return filename

def run_demo():
    print("🚀 Starting Animated Demo Video Generation...")
    
    # 1. Get Topic
    topic = "মহাকাশের ৫টি রহস্যময় তথ্য"
    print(f"Topic: {topic}")
    
    # 2. Generate Script using Gemini
    try:
        script = generate_script(topic)
    except Exception as e:
        print(f"Error generating script: {e}")
        return

    # Create directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    image_paths = []
    audio_paths = []
    
    # 3. Process Assets
    for i, scene in enumerate(script['scenes']):
        print(f"Preparing Assets for Scene {i+1}...")
        
        # Voiceover using gTTS
        voice_path = f"temp/voice_{i}.mp3"
        tts = gTTS(text=scene['narration'], lang='bn')
        tts.save(voice_path)
        audio_paths.append(voice_path)
        
        # Background Image
        img_path = f"temp/bg_{i}.png"
        create_dummy_background(f"Scene {i+1}: {scene['visual_description'][:30]}...", img_path)
        image_paths.append(img_path)

    # 4. Create Video using the updated video_editor
    print("🎬 Assembling Animated Video...")
    output_filename = "animated_demo_video.mp4"
    output_path = create_video(script['scenes'], image_paths, audio_paths, output_filename)
    
    print(f"✅ Animated Demo Video Created: {output_path}")

if __name__ == "__main__":
    run_demo()
