# modules/video_editor.py
# Images + Voiceover + Music মিলিয়ে final video বানায়

import os
import random
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, VideoFileClip
)
from moviepy.audio.fx.all import audio_loop, volumex
from PIL import Image, ImageDraw, ImageFont
import numpy as np

OUTPUT_DIR = "output"
MUSIC_DIR = "music"

def add_ken_burns_effect(image_path: str, duration: float, zoom_direction: str = "in") -> ImageClip:
    """
    Static image-এ Ken Burns effect যোগ করে (zoom in/out + pan)
    এতে animation-এর মতো দেখায়
    """
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    W, H = img.size

    def make_frame(t):
        progress = t / duration
        if zoom_direction == "in":
            scale = 1.0 + 0.1 * progress
        elif zoom_direction == "out":
            scale = 1.1 - 0.1 * progress
        else:  # pan
            scale = 1.05

        new_w = int(W * scale)
        new_h = int(H * scale)
        resized = Image.fromarray(img_array).resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        left = (new_w - W) // 2
        top = (new_h - H) // 2

        # Pan effect
        if zoom_direction == "pan_right":
            left = int(progress * (new_w - W))
        elif zoom_direction == "pan_left":
            left = int((1 - progress) * (new_w - W))

        cropped = resized.crop((left, top, left + W, top + H))
        return np.array(cropped)

    return ImageClip(make_frame, duration=duration, ismask=False)


def add_subtitle_overlay(clip, text: str, duration: float):
    """Scene-এ subtitle যোগ করে"""
    # Simple subtitle at bottom
    from moviepy.editor import TextClip, CompositeVideoClip

    try:
        txt = TextClip(
            text[:80],  # First 80 chars
            fontsize=36,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(clip.w - 100, None)
        ).set_duration(duration).set_position(('center', 'bottom')).set_margin(bottom=40)

        return CompositeVideoClip([clip, txt])
    except:
        return clip  # Subtitle ছাড়াই চলবে


def create_video(scenes: list, image_paths: list, audio_paths: list, output_filename: str, music_path: str = None) -> str:
    """
    সব কিছু মিলিয়ে final video তৈরি করে
    """
    print(f"\n🎬 Video তৈরি হচ্ছে...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    zoom_effects = ["in", "out", "pan_right", "pan_left", "in", "out"]
    clips = []

    for i, (scene, img_path, audio_path) in enumerate(zip(scenes, image_paths, audio_paths)):
        print(f"  🎞️ Scene {i+1}/{len(scenes)} processing...")

        try:
            # Audio duration বের করা
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 0.5  # একটু extra

            # Image-এ animation effect
            effect = zoom_effects[i % len(zoom_effects)]
            video_clip = add_ken_burns_effect(img_path, duration, effect)
            video_clip = video_clip.set_fps(24)

            # Audio যোগ
            video_clip = video_clip.set_audio(audio_clip)

            # Fade in/out
            video_clip = video_clip.fadein(0.5).fadeout(0.5)

            clips.append(video_clip)

        except Exception as e:
            print(f"  ⚠️ Scene {i+1} error: {e}")
            # Fallback clip
            fallback = ImageClip(img_path, duration=5).set_fps(24)
            clips.append(fallback)

    # সব clip জোড়া লাগানো
    print("  🔗 Clips জোড়া লাগানো হচ্ছে...")
    final_video = concatenate_videoclips(clips, method="compose")

    # Background music যোগ
    final_video = add_background_music(final_video, music_path)

    # Output path
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Video export
    print("  💾 Video export হচ্ছে (এটা কিছুটা সময় নেবে)...")
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp/temp_audio.m4a",
        remove_temp=True,
        preset="medium",
        bitrate="4000k",
        logger=None
    )

    print(f"  ✅ Video তৈরি হয়েছে: {output_path}")
    return output_path


def add_background_music(video_clip, music_path: str = None):
    """Background music যোগ করে"""
    # Explicit path না থাকলে music/ folder থেকে random বাছে
    if not music_path:
        if os.path.exists(MUSIC_DIR):
            files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
            if files:
                music_path = os.path.join(MUSIC_DIR, random.choice(files))

    if not music_path or not os.path.exists(music_path):
        print("  ℹ️ কোনো music নেই, music ছাড়াই চলবে")
        return video_clip

    print(f"  🎵 Background music মেশানো হচ্ছে: {os.path.basename(music_path)}")

    try:
        music = AudioFileClip(music_path)

        # Video duration-এ loop করা
        if music.duration < video_clip.duration:
            music = audio_loop(music, duration=video_clip.duration)
        else:
            music = music.subclip(0, video_clip.duration)

        # Volume কমানো (background এ থাকবে)
        music = volumex(music, 0.15)

        # Original voiceover + music mix
        if video_clip.audio:
            mixed = CompositeAudioClip([video_clip.audio, music])
            return video_clip.set_audio(mixed)
    except Exception as e:
        print(f"  ⚠️ Music error: {e}")

    return video_clip


def create_intro_clip(channel_name: str = "আমার চ্যানেল") -> ImageClip:
    """Channel intro ক্লিপ বানায়"""
    img = Image.new('RGB', (1920, 1080), color=(13, 13, 20))
    draw = ImageDraw.Draw(img)

    # Simple gradient-like background
    for y in range(1080):
        r = int(13 + (y / 1080) * 30)
        g = int(13 + (y / 1080) * 10)
        b = int(20 + (y / 1080) * 40)
        draw.line([(0, y), (1920, y)], fill=(r, g, b))

    img_array = np.array(img)
    intro = ImageClip(img_array, duration=2).set_fps(24)
    return intro.fadein(0.3).fadeout(0.3)
