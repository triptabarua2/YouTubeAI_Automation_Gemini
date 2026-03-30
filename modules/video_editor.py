# modules/video_editor.py
# FUNNY Animation Video — emotion-based character animations
#
# Emotions:
#   shocked       → jump up + shake
#   laughing      → fast bounce + wobble
#   facepalm      → lean + droop
#   jumping       → big bounce loop
#   confused      → head tilt
#   proud         → puff up
#   scared        → rapid shake
#   crying_laugh  → bounce + tilt
#   default       → breathing + talking pulse

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    VideoClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, CompositeVideoClip
)

OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
CHAR_CACHE = os.path.join(ASSETS_DIR, "character_transparent.png")
VIDEO_W, VIDEO_H = 1920, 1080


# ── 1. Background Remove ──────────────────────────────────────

def remove_white_background(src: str, dst: str, threshold: int = 230) -> str:
    img  = Image.open(src).convert("RGBA")
    data = np.array(img, dtype=np.float32)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    white = (r > threshold) & (g > threshold) & (b > threshold)
    mask  = Image.fromarray(white.astype(np.uint8) * 255, "L")
    mask  = mask.filter(ImageFilter.GaussianBlur(radius=1))
    data[:,:,3] = a * (1 - np.array(mask) / 255.0)
    Image.fromarray(data.astype(np.uint8), "RGBA").save(dst, "PNG")
    print(f"  ✅ Background removed → {dst}")
    return dst


def get_character_image():
    src = os.path.join(ASSETS_DIR, "character.png")
    if not os.path.exists(src):
        print("  ⚠️ character.png নেই"); return None
    if not os.path.exists(CHAR_CACHE):
        os.makedirs(ASSETS_DIR, exist_ok=True)
        remove_white_background(src, CHAR_CACHE)
    return Image.open(CHAR_CACHE).convert("RGBA")


# ── 2. Background Ken Burns ───────────────────────────────────

def make_background_clip(image_path: str, duration: float, effect: str) -> VideoClip:
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    arr  = np.array(img)

    def frame(t):
        p = t / duration
        scale = {"in": 1.0+0.12*p, "out": 1.12-0.12*p,
                 "pan_right": 1.1, "pan_left": 1.1}.get(effect, 1.05)
        nw, nh = int(W*scale), int(H*scale)
        res  = Image.fromarray(arr).resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw-W)//2; top = (nh-H)//2
        if effect == "pan_right": left = int(p*(nw-W))
        if effect == "pan_left":  left = int((1-p)*(nw-W))
        return np.array(res.crop((left, top, left+W, top+H)))

    return VideoClip(frame, duration=duration).with_fps(24)


# ── 3. Emotion Animations ─────────────────────────────────────

def emotion_transform(emotion: str, t: float, duration: float):
    """Returns (dx, dy, scale, rotation_deg)"""
    e = emotion.lower()

    if e == "shocked":
        jump  = -45 * math.exp(-8*(t-0.15)**2) if t < 0.6 else 0
        shake = 4 * math.sin(2*math.pi*12*t) * math.exp(-5*t)
        scale = 1.0 + 0.10 * math.exp(-6*(t-0.15)**2)
        return (shake, jump, scale, shake*0.5)

    elif e == "laughing":
        bounce = -20 * abs(math.sin(2*math.pi*4*t))
        wobble = 7  * math.sin(2*math.pi*4*t)
        return (0, bounce, 1.0, wobble)

    elif e == "facepalm":
        lean = -35 * min(t/0.5, 1)
        drp  =  18 * min(t/0.5, 1)
        rot  = -12 * min(t/0.5, 1)
        return (lean, drp, 1.0-0.04*min(t/0.5,1), rot)

    elif e == "jumping":
        bounce = -60 * abs(math.sin(2*math.pi*1.8*t))
        sc     = 1.0 + 0.06 * abs(math.sin(2*math.pi*1.8*t))
        return (0, bounce, sc, 0)

    elif e == "confused":
        tilt = 18 * math.sin(2*math.pi*0.7*t)
        return (0, 0, 1.0, tilt)

    elif e == "proud":
        rise = -12 * min(t/0.7, 1)
        sc   = 1.0 + 0.09 * min(t/0.7, 1)
        return (0, rise, sc, 0)

    elif e == "scared":
        shake = 9 * math.sin(2*math.pi*14*t)
        sc    = 1.0 - 0.04*abs(math.sin(2*math.pi*14*t))
        return (shake, 0, sc, 0)

    elif e == "crying_laugh":
        bounce = -14 * abs(math.sin(2*math.pi*3*t))
        tilt   =  8  * math.sin(2*math.pi*1.5*t)
        return (5*math.sin(2*math.pi*3*t), bounce, 1.0, tilt)

    else:  # default: breathing + talking
        return (
            3  * math.sin(2*math.pi*0.2*t),
            5  * math.sin(2*math.pi*0.4*t),
            1.0 + 0.012 * math.sin(2*math.pi*3.5*t),
            0
        )


def make_character_clip(char_img: Image.Image, duration: float,
                         emotion: str, side: str, entrance: bool) -> VideoClip:
    target_h = int(VIDEO_H * 0.65)
    target_w = int(char_img.width * (target_h / char_img.height))
    char_r   = char_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    margin = 50
    base_x = (VIDEO_W - target_w - margin) if side == "right" else margin
    base_y = VIDEO_H - target_h
    entrance_dur = 0.45

    def make_frame(t):
        # entrance slide
        if entrance and t < entrance_dur:
            ease    = 1 - (1 - t/entrance_dur)**3
            slide_y = int((1-ease)*(target_h + 80))
        else:
            slide_y = 0

        dx, dy, scale, rot = emotion_transform(emotion, t, duration)

        cur_w = int(target_w * scale)
        cur_h = int(target_h * scale)
        ch = char_r.resize((cur_w, cur_h), Image.Resampling.LANCZOS) if abs(scale-1)>0.005 else char_r.copy()

        if abs(rot) > 0.1:
            ch = ch.rotate(rot, resample=Image.Resampling.BICUBIC,
                            expand=False, center=(cur_w//2, cur_h))

        cx = int(base_x + dx) + (target_w - cur_w)//2
        cy = int(base_y + dy) + slide_y + (target_h - cur_h)

        canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
        canvas.paste(ch, (cx, cy), ch)
        return np.array(canvas)

    rgb  = VideoClip(lambda t: make_frame(t)[:,:,:3], duration=duration)
    mask = VideoClip(lambda t: make_frame(t)[:,:,3]/255.0, duration=duration, is_mask=True)
    return rgb.with_mask(mask).with_fps(24)


# ── 4. Funny Subtitle ─────────────────────────────────────────

def make_subtitle_clip(narration: str, joke: str, duration: float) -> VideoClip:
    bar_h = 115

    def make_frame(t):
        canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
        draw   = ImageDraw.Draw(canvas)

        for y in range(bar_h):
            alpha = int(195 * (1 - y/bar_h*0.4))
            draw.line([(0, VIDEO_H-bar_h+y), (VIDEO_W, VIDEO_H-bar_h+y)],
                      fill=(10, 10, 40, alpha))

        text = narration[:70] + "..." if len(narration) > 70 else narration
        try:
            font = ImageFont.load_default(size=33)
        except TypeError:
            font = ImageFont.load_default()

        draw.text((VIDEO_W//2+2, VIDEO_H-bar_h//2+2), text,
                  fill=(0,0,0,200), anchor="mm", font=font)
        draw.text((VIDEO_W//2, VIDEO_H-bar_h//2), text,
                  fill=(255,255,255,255), anchor="mm", font=font)

        # joke flash শেষ ১.৫s
        if joke and t > duration - 1.5:
            blink = int(t * 6) % 2 == 0
            jcolor = (255, 230, 50, 230) if blink else (255, 200, 0, 220)
            try:
                jfont = ImageFont.load_default(size=28)
            except TypeError:
                jfont = ImageFont.load_default()
            draw.text((VIDEO_W//2, VIDEO_H-bar_h-30),
                      f"😂 {joke[:60]}", fill=jcolor, anchor="mm", font=jfont)

        return np.array(canvas)

    rgb  = VideoClip(lambda t: make_frame(t)[:,:,:3], duration=duration)
    mask = VideoClip(lambda t: make_frame(t)[:,:,3]/255.0, duration=duration, is_mask=True)
    return rgb.with_mask(mask).with_fps(24)


# ── 5. Main ───────────────────────────────────────────────────

def create_video(scenes: list, image_paths: list, audio_paths: list,
                 output_filename: str, music_path: str = None) -> str:

    print("\n🎬 Funny Character Video তৈরি হচ্ছে...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    char_img = get_character_image()
    effects  = ["in", "out", "pan_right", "pan_left"]
    sides    = ["right", "left"]
    clips    = []

    for i, (scene, img_path, audio_path) in enumerate(
            zip(scenes, image_paths, audio_paths)):

        emotion = scene.get("character_emotion", "default")
        joke    = scene.get("joke", "")
        print(f"  🎭 Scene {i+1}/{len(scenes)} — {emotion}")

        try:
            audio = AudioFileClip(audio_path)
            dur   = audio.duration

            bg     = make_background_clip(img_path, dur, effects[i % len(effects)])
            layers = [bg]

            if char_img is not None:
                char_clip = make_character_clip(
                    char_img, dur, emotion,
                    side     = sides[i % len(sides)],
                    entrance = (i == 0)
                )
                layers.append(char_clip)

            sub = make_subtitle_clip(scene["narration"], joke, dur)
            layers.append(sub)

            comp = CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
            comp = comp.with_audio(audio).with_fps(24)
            clips.append(comp)

        except Exception as e:
            print(f"  ⚠️ Scene {i+1} error: {e}")
            import traceback; traceback.print_exc()

    if not clips:
        raise ValueError("কোনো clip তৈরি হয়নি!")

    print("  🔗 Clips জোড়া লাগানো হচ্ছে...")
    final = concatenate_videoclips(clips, method="compose")

    if music_path and os.path.exists(music_path):
        try:
            from moviepy import concatenate_audioclips
            bgm = AudioFileClip(music_path).with_volume_scaled(0.12)
            if bgm.duration < final.duration:
                n   = int(final.duration / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * n)
            bgm   = bgm.with_section(0, final.duration)
            final = final.with_audio(CompositeAudioClip([final.audio, bgm]))
        except Exception as e:
            print(f"  ⚠️ Music error: {e}")

    out = os.path.join(OUTPUT_DIR, output_filename)
    print("  💾 Export হচ্ছে...")
    final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", logger=None)
    print(f"  ✅ Done: {out}")
    return out
