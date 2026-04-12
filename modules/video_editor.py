# modules/video_editor.py
"""
Animation Video Editor — Full Pipeline
Animated intro -> Ken Burns BG -> Character Emotions ->
Speech Bubble -> Typewriter Subtitle -> Particles ->
Flash Transitions -> Subscribe Outro
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from moviepy.video.VideoClip import VideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.AudioClip import CompositeAudioClip
    from moviepy.video.compositing.concatenate import concatenate_videoclips
    from moviepy.audio.compositing.concatenate import concatenate_audioclips
except ImportError:
    try:
        from moviepy.editor import (
            VideoClip, AudioFileClip, CompositeAudioClip,
            concatenate_videoclips, concatenate_audioclips,
        )
    except ImportError:
        raise ImportError("MoviePy not installed. Run: pip install moviepy==1.0.3")

from modules.animation_effects import (
    ParticleSystem,
    make_speech_bubble_array,
    make_subtitle_array,
    make_badge_array,
    make_intro_frame,
    make_outro_frame,
    make_flash_array,
    load_font,
    ease_out_cubic,
    get_bg,
)

OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
CHAR_CACHE  = os.path.join(ASSETS_DIR, "character_transparent.png")
VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24


# MoviePy v1/v2 compat
def _fps(c):   return c.with_fps(FPS) if hasattr(c,"with_fps") else c.set_fps(FPS)
def _aud(c,a): return c.with_audio(a) if hasattr(c,"with_audio") else c.set_audio(a)
def _sub(c,s,e): return c.subclipped(s,e) if hasattr(c,"subclipped") else c.subclip(s,e)
def _vol(c,f):
    if hasattr(c,"with_volume_scaled"): return c.with_volume_scaled(f)
    if hasattr(c,"volumex"):            return c.volumex(f)
    return c


# Character loading
def _remove_bg(src, dst, thr=228):
    img  = Image.open(src).convert("RGBA")
    data = np.array(img, dtype=np.float32)
    r,g,b,a = data[:,:,0],data[:,:,1],data[:,:,2],data[:,:,3]
    white = (r>thr)&(g>thr)&(b>thr)
    mask  = Image.fromarray(white.astype(np.uint8)*255,"L").filter(ImageFilter.GaussianBlur(1.5))
    data[:,:,3] = a * (1 - np.array(mask)/255.0)
    Image.fromarray(data.astype(np.uint8),"RGBA").save(dst,"PNG")

def _get_char():
    src = os.path.join(ASSETS_DIR,"character.png")
    if not os.path.exists(src): return None
    if not os.path.exists(CHAR_CACHE):
        os.makedirs(ASSETS_DIR,exist_ok=True)
        _remove_bg(src,CHAR_CACHE)
    return Image.open(CHAR_CACHE).convert("RGBA")


# Ken Burns background
def _make_bg_fn(img_path, duration, effect):
    img = Image.open(img_path).convert("RGB")
    W,H = img.size; arr = np.array(img)
    def frame(t):
        p = t/max(duration,0.01)
        scale = {"zoom_in":1.0+0.12*p,"zoom_out":1.12-0.12*p,
                 "pan_right":1.10,"pan_left":1.10}.get(effect,1.05)
        nw=max(W,int(W*scale)); nh=max(H,int(H*scale))
        res  = Image.fromarray(arr).resize((nw,nh),Image.Resampling.LANCZOS)
        left = (nw-W)//2; top=(nh-H)//2
        if effect=="pan_right": left=int(p*(nw-W))
        if effect=="pan_left":  left=int((1-p)*(nw-W))
        return np.array(res.crop((left,top,left+W,top+H)))
    return frame


# Emotion transforms
_E = {
    "shocked":      lambda t,d:(5*math.sin(2*math.pi*12*t)*math.exp(-4*t),-42*math.exp(-7*(t-0.18)**2) if t<0.7 else 0,1.0+0.12*math.exp(-5*(t-0.18)**2),4*math.sin(2*math.pi*12*t)*math.exp(-4*t)*0.5),
    "laughing":     lambda t,d:(0,-20*abs(math.sin(2*math.pi*4*t)),1.0,7*math.sin(2*math.pi*4*t)),
    "facepalm":     lambda t,d:(-32*min(t/0.5,1),17*min(t/0.5,1),1.0-0.04*min(t/0.5,1),-13*min(t/0.5,1)),
    "jumping":      lambda t,d:(0,-68*abs(math.sin(2*math.pi*1.8*t)),1.0+0.07*abs(math.sin(2*math.pi*1.8*t)),0),
    "confused":     lambda t,d:(0,0,1.0,18*math.sin(2*math.pi*0.7*t)),
    "proud":        lambda t,d:(0,-15*min(t/0.8,1),1.0+0.10*min(t/0.8,1),0),
    "scared":       lambda t,d:(10*math.sin(2*math.pi*14*t),0,1.0-0.05*abs(math.sin(2*math.pi*14*t)),0),
    "crying_laugh": lambda t,d:(6*math.sin(2*math.pi*3*t),-14*abs(math.sin(2*math.pi*3*t)),1.0,8*math.sin(2*math.pi*1.5*t)),
}
def _emotion(em,t,d):
    fn=_E.get(em.lower())
    if fn:
        try: return fn(t,d)
        except: pass
    return (3*math.sin(2*math.pi*0.22*t),5*math.sin(2*math.pi*0.42*t),1.0+0.013*math.sin(2*math.pi*3.5*t),0)


# Character frame function
def _make_char_fn(char_img, duration, emotion, side, entrance):
    TH=int(VIDEO_H*0.65); TW=int(char_img.width*(TH/char_img.height))
    base=char_img.resize((TW,TH),Image.Resampling.LANCZOS)
    M=55; bx=(VIDEO_W-TW-M) if side=="right" else M; by=VIDEO_H-TH; ENT=0.45

    def frame(t):
        sl=0
        if entrance and t<ENT: sl=int((1-ease_out_cubic(t/ENT))*(TH+80))
        dx,dy,scale,rot=_emotion(emotion,t,duration)
        cw=int(TW*scale); ch=int(TH*scale)
        ci=base.resize((cw,ch),Image.Resampling.LANCZOS) if abs(scale-1)>0.004 else base.copy()
        if abs(rot)>0.12: ci=ci.rotate(rot,resample=Image.Resampling.BICUBIC,expand=False,center=(cw//2,ch))
        cx2=int(bx+dx)+(TW-cw)//2; cy2=int(by+dy)+sl+(TH-ch)
        canvas=Image.new("RGBA",(VIDEO_W,VIDEO_H),(0,0,0,0))
        canvas.paste(ci,(cx2,cy2),ci)
        return np.array(canvas)
    return frame


# Scene frame compositor
def _make_scene_fn(scene, img_path, duration, char_img, font_path, topic, idx, total):
    EFFECTS=["zoom_in","zoom_out","pan_right","pan_left"]
    SIDES=["right","left"]
    emotion=scene.get("character_emotion","default")
    side=SIDES[idx%len(SIDES)]; effect=EFFECTS[idx%len(EFFECTS)]
    entrance=(idx==0)

    bg_fn   = _make_bg_fn(img_path,duration,effect)
    char_fn = _make_char_fn(char_img,duration,emotion,side,entrance) if char_img else None
    ps      = ParticleSystem(n=18,w=VIDEO_W,h=VIDEO_H,topic=topic,seed=idx*7+3)

    font=load_font(font_path,46); joke_f=load_font(font_path,36)
    badge_f=load_font(font_path,28); bubble_f=load_font(font_path,32)

    bubble_text=scene.get("narration","")[:60]
    bx=(VIDEO_W-790) if side=="right" else 790
    by=VIDEO_H-int(VIDEO_H*0.38)
    show_bubble=(topic=="funny")
    bubble_end=duration*0.60

    def make_frame(t):
        canvas=Image.fromarray(bg_fn(t)).convert("RGBA")

        if show_bubble and t<bubble_end:
            bub_arr=make_speech_bubble_array(bubble_text,bx,by,VIDEO_W,VIDEO_H,side=side,font=bubble_f,bw=460)
            bub_img=Image.fromarray(bub_arr,"RGBA")
            if t<0.5:
                a=int(255*ease_out_cubic(t/0.5))
                bub_img.putalpha(Image.new("L",bub_img.size,a))
            canvas.paste(bub_img,(0,0),bub_img)

        if char_fn:
            ci=Image.fromarray(char_fn(t),"RGBA")
            canvas.paste(ci,(0,0),ci)

        p_img=Image.fromarray(ps.get_frame(t),"RGBA")
        canvas.paste(p_img,(0,0),p_img)

        sub_img=Image.fromarray(make_subtitle_array(scene,t,VIDEO_W,VIDEO_H,font,joke_f),"RGBA")
        canvas.paste(sub_img,(0,0),sub_img)

        badge_img=Image.fromarray(make_badge_array(idx+1,total,t,VIDEO_W,VIDEO_H,badge_f,topic),"RGBA")
        canvas.paste(badge_img,(0,0),badge_img)

        return np.array(canvas.convert("RGB"))

    return make_frame


# Main
def create_video(scenes, image_paths, audio_paths,
                 output_filename, music_path=None,
                 output_dir=None, topic="funny"):
    out=output_dir or OUTPUT_DIR
    os.makedirs(out,exist_ok=True)
    try:
        from config import FONT_PATH
        font_path=FONT_PATH if os.path.exists(FONT_PATH) else None
    except Exception:
        font_path=None

    print(f"\n🎬 Animation Video তৈরি হচ্ছে... [{topic}]")
    char_img=_get_char()
    if char_img: print("  ✅ Character loaded")
    else:        print("  ⚠  character.png নেই")

    INTRO_D=3.5; OUTRO_D=4.0; TRANS_D=0.25
    clips=[]

    # Intro
    title=scenes[0].get("visual_description","Animation")[:45] if scenes else "Animation"
    intro=VideoClip(make_frame=lambda t:make_intro_frame(t,title,INTRO_D,VIDEO_W,VIDEO_H,font_path,topic),duration=INTRO_D)
    clips.append(_fps(intro)); print("  ✅ Intro তৈরি")

    # Scenes
    for i,(scene,img_path,audio_path) in enumerate(zip(scenes,image_paths,audio_paths)):
        print(f"  🎭 Scene {i+1}/{len(scenes)} — {scene.get('character_emotion','default')}")
        try:
            audio=AudioFileClip(audio_path); dur=audio.duration
        except Exception as e:
            print(f"  ⚠  Audio error: {e}"); continue

        scene_fn=_make_scene_fn(scene,img_path,dur,char_img,font_path,topic,i,len(scenes))

        flash=VideoClip(make_frame=lambda t:np.array(Image.fromarray(make_flash_array(t,TRANS_D,VIDEO_W,VIDEO_H)).convert("RGB")),duration=TRANS_D)
        clips.append(_fps(flash))

        sc=VideoClip(make_frame=scene_fn,duration=dur)
        clips.append(_fps(_aud(sc,audio)))

    # Outro
    dark=VideoClip(make_frame=lambda t:np.array(Image.fromarray(make_flash_array(t,TRANS_D,VIDEO_W,VIDEO_H,(0,0,0))).convert("RGB")),duration=TRANS_D)
    clips.append(_fps(dark))
    outro=VideoClip(make_frame=lambda t:make_outro_frame(t,OUTRO_D,VIDEO_W,VIDEO_H,font_path,topic),duration=OUTRO_D)
    clips.append(_fps(outro)); print("  ✅ Outro তৈরি")

    if not clips: raise ValueError("কোনো clip নেই!")

    print("  🔗 Clips জোড়া লাগানো হচ্ছে...")
    final=concatenate_videoclips(clips,method="compose")

    if music_path and os.path.exists(music_path):
        try:
            bgm=_vol(AudioFileClip(music_path),0.10)
            if bgm.duration<final.duration:
                n=int(final.duration/bgm.duration)+1
                bgm=concatenate_audioclips([bgm]*n)
            bgm=_sub(bgm,0,final.duration)
            final=_aud(final,CompositeAudioClip([final.audio,bgm]) if final.audio else bgm)
        except Exception as e:
            print(f"  ⚠  Music: {e}")

    out_path=os.path.join(out,output_filename)
    print("  💾 Exporting...")
    final.write_videofile(out_path,fps=FPS,codec="libx264",audio_codec="aac",preset="medium",logger=None)
    print(f"  ✅ Done -> {out_path}")
    return out_path
