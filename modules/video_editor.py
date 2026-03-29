# modules/video_editor.py
# Images + Voiceover + Music + Character Overlay + Animation Effects

import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip, ImageClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, VideoFileClip, CompositeVideoClip,
    ColorClip
)

OUTPUT_DIR = "output"
MUSIC_DIR = "music"
ASSETS_DIR = "assets"

def add_ken_burns_effect(image_path: str, duration: float, zoom_direction: str = "in") -> VideoClip:
    """
    Static image-এ Ken Burns effect যোগ করে (zoom in/out + pan)
    """
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    img_array = np.array(img)

    def make_frame(t):
        progress = t / duration
        if zoom_direction == "in":
            scale = 1.0 + 0.15 * progress
        elif zoom_direction == "out":
            scale = 1.15 - 0.15 * progress
        else:  # pan
            scale = 1.1

        new_w = int(W * scale)
        new_h = int(H * scale)
        resized = Image.fromarray(img_array).resize((new_w, new_h), Image.Resampling.LANCZOS)

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

    return VideoClip(make_frame, duration=duration)

def add_character_overlay(video_clip, character_path: str, position: str = "right"):
    """ভিডিওর ওপর ক্যারেক্টার বসায়"""
    if not os.path.exists(character_path):
        return video_clip

    char_img = Image.open(character_path).convert("RGBA")
    # Resize character to fit height (approx 70% of video height)
    target_h = int(video_clip.h * 0.7)
    w_percent = (target_h / float(char_img.size[1]))
    target_w = int((float(char_img.size[0]) * float(w_percent)))
    char_img = char_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    char_array = np.array(char_img)
    # Separate RGB and Alpha for MoviePy 2.x
    rgb = char_array[:, :, :3]
    alpha = char_array[:, :, 3] / 255.0
    
    char_clip = ImageClip(rgb, duration=video_clip.duration)
    mask_clip = ImageClip(alpha, is_mask=True, duration=video_clip.duration)
    char_clip = char_clip.with_mask(mask_clip)
    
    # Position
    if position == "right":
        pos_x = video_clip.w - target_w - 50
        pos_y = video_clip.h - target_h
    elif position == "left":
        pos_x = 50
        pos_y = video_clip.h - target_h
    else:
        pos_x = (video_clip.w - target_w) // 2
        pos_y = video_clip.h - target_h
        
    # Add a slight "breathing" animation to character
    def breathe(t):
        y_offset = int(5 * np.sin(2 * np.pi * 0.5 * t)) # 0.5Hz breathing
        return (pos_x, pos_y + y_offset)
    
    char_clip = char_clip.with_position(breathe)
    
    return CompositeVideoClip([video_clip, char_clip])

def add_subtitle_overlay(video_clip, text: str):
    """ভিডিওর নিচে সাবটাইটেল যোগ করে"""
    duration = video_clip.duration
    W, H = video_clip.size
    
    def make_subtitle_frame(t):
        # Create a transparent layer
        sub_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sub_img)
        
        # Draw black bar at bottom
        bar_h = 100
        draw.rectangle([0, H - bar_h, W, H], fill=(0, 0, 0, 160))
        
        # Draw text
        try:
            font = ImageFont.load_default()
            draw.text((W//2, H - bar_h//2), text[:60], fill=(255, 255, 255, 255), anchor="mm", font=font)
        except:
            pass
            
        return np.array(sub_img)

    def make_subtitle_mask(t):
        sub_img = Image.new('L', (W, H), 0)
        draw = ImageDraw.Draw(sub_img)
        bar_h = 100
        draw.rectangle([0, H - bar_h, W, H], fill=160)
        return np.array(sub_img) / 255.0

    sub_clip = VideoClip(make_subtitle_frame, duration=duration)
    sub_mask = VideoClip(make_subtitle_mask, duration=duration, is_mask=True)
    sub_clip = sub_clip.with_mask(sub_mask)
    
    return CompositeVideoClip([video_clip, sub_clip])

def create_video(scenes: list, image_paths: list, audio_paths: list, output_filename: str, music_path: str = None) -> str:
    """সব কিছু মিলিয়ে final video তৈরি করে"""
    print(f"\n🎬 Video তৈরি হচ্ছে...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    char_path = os.path.join(ASSETS_DIR, "character.png")
    zoom_effects = ["in", "out", "pan_right", "pan_left"]
    clips = []

    for i, (scene, img_path, audio_path) in enumerate(zip(scenes, image_paths, audio_paths)):
        print(f"  🎞️ Scene {i+1}/{len(scenes)} processing...")
        
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # 1. Background with Ken Burns
            effect = zoom_effects[i % len(zoom_effects)]
            video_clip = add_ken_burns_effect(img_path, duration, effect)
            video_clip = video_clip.with_fps(24)
            
            # 2. Add Character Overlay
            video_clip = add_character_overlay(video_clip, char_path, position="right" if i % 2 == 0 else "left")
            
            # 3. Add Subtitles
            video_clip = add_subtitle_overlay(video_clip, scene['narration'])
            
            # 4. Set Audio
            video_clip = video_clip.with_audio(audio_clip)
            
            # 5. Simple Opacity Fade (Manual)
            def fade_opacity(t):
                if t < 0.5: return t / 0.5
                if t > duration - 0.5: return (duration - t) / 0.5
                return 1.0
            
            # Applying manual fade via mask multiplication
            # (Simplified for this demo to avoid more import errors)
            
            clips.append(video_clip)
            
        except Exception as e:
            print(f"  ⚠️ Scene {i+1} error: {e}")

    if not clips:
        raise ValueError("No clips were generated!")

    print("  🔗 Clips জোড়া লাগানো হচ্ছে...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Background music
    if music_path and os.path.exists(music_path):
        bg_music = AudioFileClip(music_path).with_volume_scaled(0.1)
        if bg_music.duration < final_video.duration:
            bg_music = bg_music.with_duration(final_video.duration)
        else:
            bg_music = bg_music.with_section(0, final_video.duration)
            
        final_audio = CompositeAudioClip([final_video.audio, bg_music])
        final_video = final_video.with_audio(final_audio)

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print("  💾 Video export হচ্ছে...")
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    return output_path
