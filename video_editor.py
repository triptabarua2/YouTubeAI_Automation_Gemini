# modules/video_editor.py
# FUNNY Animation Video — emotion-based character animations with multi-language subtitles

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    # Try MoviePy v2 imports
    from moviepy.video.VideoClip import VideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.AudioClip import CompositeAudioClip
    from moviepy.video.compositing.concatenate import concatenate_videoclips
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.compositing.concatenate import concatenate_audioclips
except ImportError:
    # Fallback to MoviePy v1 imports
    try:
        from moviepy.editor import (
            VideoClip, AudioFileClip, CompositeAudioClip,
            concatenate_videoclips, CompositeVideoClip, concatenate_audioclips
        )
    except ImportError:
        raise ImportError("MoviePy is not installed correctly. Please install it using 'pip install moviepy'.")

# ── MoviePy version detection ──────────────────────────────────
import moviepy as _moviepy_module
_MOVIEPY_MAJOR = int(_moviepy_module.__version__.split(".")[0])
_MOVIEPY_V2 = _MOVIEPY_MAJOR >= 2

# PIL Resampling compatibility (Pillow < 9.1 uses Image.LANCZOS directly)
try:
    _LANCZOS = Image.Resampling.LANCZOS
    _BICUBIC = Image.Resampling.BICUBIC
except AttributeError:
    _LANCZOS = Image.LANCZOS
    _BICUBIC = Image.BICUBIC

# MoviePy v1 vs v2 compatibility helpers
def _has_method(obj, method_name):
    return hasattr(obj, method_name)

def _make_video_clip(make_frame_func, duration):
    """MoviePy v1/v2 compatible VideoClip constructor."""
    if _MOVIEPY_V2:
        return VideoClip(frame_function=make_frame_func, duration=duration)
    else:
        return VideoClip(make_frame=make_frame_func, duration=duration)

def _with_fps(clip, fps):
    if _has_method(clip, "with_fps"): return clip.with_fps(fps)
    return clip.set_fps(fps)

def _with_audio(clip, audio):
    if _has_method(clip, "with_audio"): return clip.with_audio(audio)
    return clip.set_audio(audio)

def _with_mask(clip, mask):
    if _has_method(clip, "with_mask"): return clip.with_mask(mask)
    return clip.set_mask(mask)

def _subclipped(clip, start, end):
    if _has_method(clip, "subclipped"): return clip.subclipped(start, end)
    return clip.subclip(start, end)

def _with_volume_scaled(clip, factor):
    if _has_method(clip, "with_volume_scaled"): return clip.with_volume_scaled(factor)
    if _has_method(clip, "volumex"): return clip.volumex(factor)
    return clip

OUTPUT_DIR = "output"  # default
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
        res  = Image.fromarray(arr).resize((nw, nh), _LANCZOS)
        left = (nw-W)//2; top = (nh-H)//2
        if effect == "pan_right": left = int(p*(nw-W))
        if effect == "pan_left":  left = int((1-p)*(nw-W))
        return np.array(res.crop((left, top, left+W, top+H)))

    return _with_fps(_make_video_clip(frame, duration), 24)


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
    char_r   = char_img.resize((target_w, target_h), _LANCZOS)

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
        ch = char_r.resize((cur_w, cur_h), _LANCZOS) if abs(scale-1)>0.005 else char_r.copy()

        if abs(rot) > 0.1:
            ch = ch.rotate(rot, resample=_BICUBIC,
                            expand=False, center=(cur_w//2, cur_h))

        cx = int(base_x + dx) + (target_w - cur_w)//2
        cy = int(base_y + dy) + slide_y + (target_h - cur_h)

        canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
        canvas.paste(ch, (cx, cy), ch)
        return np.array(canvas)

    rgb  = _make_video_clip(lambda t: make_frame(t)[:,:,:3], duration)
    mask = _make_video_clip(lambda t: make_frame(t)[:,:,3]/255.0, duration)
    return _with_fps(_with_mask(rgb, mask), 24)


# ── 4. Multi-language Subtitle ─────────────────────────────────────────

def make_subtitle_clip(scene: dict, duration: float) -> VideoClip:
    bar_h = 80  # Smaller bar — English only

    def make_frame(t):
        canvas = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
        draw   = ImageDraw.Draw(canvas)

        # Background bar
        for y in range(bar_h):
            alpha = int(205 * (1 - y/bar_h*0.4))
            draw.line([(0, VIDEO_H-bar_h+y), (VIDEO_W, VIDEO_H-bar_h+y)],
                      fill=(5, 5, 25, alpha))

        # English only
        en_text = scene.get("translation_english", "")
        display_text = en_text[:100] + "..." if len(en_text) > 100 else en_text

        from config import FONT_PATH
        try:
            if os.path.exists(FONT_PATH):
                font = ImageFont.truetype(FONT_PATH, size=45)
            else:
                font = ImageFont.load_default(size=36)
        except:
            font = ImageFont.load_default()

        y_offset = VIDEO_H - bar_h + (bar_h // 2)

        # Shadow
        draw.text((VIDEO_W//2+2, y_offset+2), display_text, fill=(0,0,0,220), anchor="mm", font=font)
        # Main text
        draw.text((VIDEO_W//2, y_offset), display_text, fill=(255,255,255,255), anchor="mm", font=font)

        # joke flash শেষ ১.৫s
        joke = scene.get("joke", "")
        if joke and t > duration - 1.5:
            blink = int(t * 6) % 2 == 0
            jcolor = (255, 230, 50, 230) if blink else (255, 200, 0, 220)
            from config import FONT_PATH
            try:
                if os.path.exists(FONT_PATH):
                    jfont = ImageFont.truetype(FONT_PATH, size=35)
                else:
                    jfont = ImageFont.load_default(size=30)
            except:
                jfont = ImageFont.load_default()
            draw.text((VIDEO_W//2, VIDEO_H-bar_h-35), f"😂 {joke[:65]}", fill=jcolor, anchor="mm", font=jfont)

        return np.array(canvas)

    rgb  = _make_video_clip(lambda t: make_frame(t)[:,:,:3], duration)
    mask = _make_video_clip(lambda t: make_frame(t)[:,:,3]/255.0, duration)
    return _with_fps(_with_mask(rgb, mask), 24)


# ── 5. Main ───────────────────────────────────────────────────

def create_video(scenes, image_paths, audio_paths,
                 output_filename, music_path=None, output_dir=None, topic="funny"):

    out = output_dir or OUTPUT_DIR
    print("\n🎬 Multi-language Funny Video তৈরি হচ্ছে...")
    os.makedirs(out, exist_ok=True)

    # Only show character for 'funny' topic
    char_img = get_character_image() if topic == "funny" else None
    effects  = ["in", "out", "pan_right", "pan_left"]
    sides    = ["right", "left"]
    clips    = []

    for i, (scene, img_path, audio_path) in enumerate(
            zip(scenes, image_paths, audio_paths)):

        emotion = scene.get("character_emotion", "default")
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

            sub = make_subtitle_clip(scene, dur)
            layers.append(sub)

            comp = CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
            comp = _with_fps(_with_audio(comp, audio), 24)
            clips.append(comp)

        except Exception as e:
            import traceback
            print(f"  ⚠️ Scene {i+1} error: {e!r}")
            traceback.print_exc()

    if not clips:
        raise ValueError("কোনো clip তৈরি হয়নি!")

    print("  🔗 Clips জোড়া লাগানো হচ্ছে...")
    final = concatenate_videoclips(clips, method="compose")

    if music_path and os.path.exists(music_path):
        try:
            bgm = _with_volume_scaled(AudioFileClip(music_path), 0.12)
            if bgm.duration < final.duration:
                n   = int(final.duration / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * n)
            bgm   = _subclipped(bgm, 0, final.duration)
            final = _with_audio(final, CompositeAudioClip([final.audio, bgm]))
        except Exception as e:
            print(f"  ⚠️ Music error: {e}")

    out_path = os.path.join(out, output_filename)
    print("  💾 Export হচ্ছে...")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    print(f"  ✅ Done: {out_path}")
    return out_path
