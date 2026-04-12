# modules/animation_effects.py
"""
Animation Effects Library — YouTube AI Video System
সব animation helper এখানে আছে।
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ═══════════════════════════════════════════════════════════════════
#  Easing Functions
# ═══════════════════════════════════════════════════════════════════

def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4*t*t*t if t < 0.5 else 1 - (-2*t+2)**3 / 2

def ease_out_bounce(t: float) -> float:
    t = max(0.0, min(1.0, t))
    n1, d1 = 7.5625, 2.75
    if   t < 1/d1:   return n1 * t * t
    elif t < 2/d1:   t -= 1.5/d1;   return n1*t*t + 0.75
    elif t < 2.5/d1: t -= 2.25/d1;  return n1*t*t + 0.9375
    else:             t -= 2.625/d1; return n1*t*t + 0.984375

def ease_out_elastic(t: float) -> float:
    if t in (0.0, 1.0): return t
    t = max(0.0, min(1.0, t))
    return 2**(-10*t) * math.sin((t*10 - 0.75) * (2*math.pi) / 3) + 1


# ═══════════════════════════════════════════════════════════════════
#  Color Themes
# ═══════════════════════════════════════════════════════════════════

TOPIC_PALETTE = {
    "funny":         [(255, 200,  50), (255,  80, 160), ( 50, 210, 255)],
    "educational":   [( 50, 160, 255), ( 80, 230, 150), (200, 120, 255)],
    "storytelling":  [(200,  50, 255), (255,  60, 110), ( 80, 180, 255)],
}

TOPIC_BG = {
    "funny":         [(15,  15,  50), (50,  10,  80)],
    "educational":   [( 5,  25,  60), (10,  50,  40)],
    "storytelling":  [(20,   5,  40), (45,   5,  60)],
}

def get_palette(topic: str):
    return TOPIC_PALETTE.get(topic, TOPIC_PALETTE["funny"])

def get_bg(topic: str):
    return TOPIC_BG.get(topic, TOPIC_BG["funny"])

def get_accent(topic: str):
    return TOPIC_PALETTE.get(topic, TOPIC_PALETTE["funny"])[0]


# ═══════════════════════════════════════════════════════════════════
#  Image / Drawing Helpers
# ═══════════════════════════════════════════════════════════════════

def make_gradient_img(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for row in range(h):
        t = row / max(h - 1, 1)
        for ch in range(3):
            arr[row, :, ch] = int(c1[ch]*(1-t) + c2[ch]*t)
    return Image.fromarray(arr, "RGB")


def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
    except Exception:
        pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def draw_outlined_text(draw, text, pos, font,
                        fill=(255,255,255,255),
                        outline=(0,0,0,220), width=2, anchor="mm"):
    x, y = pos
    for dx in range(-width, width+1):
        for dy in range(-width, width+1):
            if dx or dy:
                draw.text((x+dx, y+dy), text, font=font, fill=outline, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


# ═══════════════════════════════════════════════════════════════════
#  Particle System — ভাসমান sparkles
# ═══════════════════════════════════════════════════════════════════

class ParticleSystem:
    def __init__(self, n: int = 22, w: int = 1920, h: int = 1080,
                 topic: str = "funny", seed: int = 42):
        self.n = n; self.w = w; self.h = h
        self.colors = TOPIC_PALETTE.get(topic, TOPIC_PALETTE["funny"])
        rng = np.random.default_rng(seed)
        self.x   = rng.uniform(0, w, n)
        self.y   = rng.uniform(0, h, n)
        self.vx  = rng.uniform(-14, 14, n)
        self.vy  = rng.uniform(-38, -8, n)
        self.sz  = rng.uniform(2.5, 7.0, n)
        self.ci  = rng.integers(0, len(self.colors), n)
        self.phi = rng.uniform(0, math.pi*2, n)

    def get_frame(self, t: float) -> np.ndarray:
        canvas = Image.new("RGBA", (self.w, self.h), (0,0,0,0))
        draw   = ImageDraw.Draw(canvas)
        for i in range(self.n):
            x = (self.x[i] + self.vx[i] * t * 8)  % self.w
            y = (self.y[i] + self.vy[i] * t * 6)  % self.h
            s = self.sz[i] * (0.75 + 0.25 * math.sin(t*3 + self.phi[i]))
            a = int(130 * (0.55 + 0.45 * math.sin(t*2.5 + self.phi[i])))
            c = self.colors[self.ci[i]]
            draw.ellipse([x-s, y-s, x+s, y+s], fill=(*c, a))
        return np.array(canvas)


# ═══════════════════════════════════════════════════════════════════
#  Speech Bubble
# ═══════════════════════════════════════════════════════════════════

def _wrap(text, font, draw, max_px):
    words = text.split(); lines = []; cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        try:
            bb = draw.textbbox((0,0), test, font=font)
            tw = bb[2] - bb[0]
        except Exception:
            tw = len(test) * 12
        if tw > max_px and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur: lines.append(cur)
    return lines[:3]


def make_speech_bubble_array(text: str, cx: int, bottom_y: int,
                               w_total: int, h_total: int,
                               side: str = "left",
                               font=None, bw: int = 460) -> np.ndarray:
    """Returns RGBA numpy array with just the speech bubble drawn."""
    canvas = Image.new("RGBA", (w_total, h_total), (0,0,0,0))
    if not text or not text.strip():
        return np.array(canvas)

    draw = ImageDraw.Draw(canvas, "RGBA")
    if font is None:
        font = ImageFont.load_default()

    lines = _wrap(text, font, draw, bw - 40)
    lh = 38; pad = 18
    bh = len(lines) * lh + pad * 2
    x1 = cx - bw//2; y1 = bottom_y - bh
    x2 = cx + bw//2; y2 = bottom_y

    # Shadow
    draw.rounded_rectangle([x1+5, y1+5, x2+5, y2+5], radius=22, fill=(0,0,0,70))
    # Body
    draw.rounded_rectangle([x1, y1, x2, y2], radius=22,
                             fill=(255,255,255,238),
                             outline=(55,55,100,210), width=3)
    # Pointer
    px = (x1 + 80) if side == "left" else (x2 - 80)
    pts = [(px-14, y2), (px+14, y2), (px, y2+26)]
    draw.polygon(pts, fill=(255,255,255,238))
    draw.line([(px-14,y2),(px,y2+26)], fill=(55,55,100,210), width=3)
    draw.line([(px+14,y2),(px,y2+26)], fill=(55,55,100,210), width=3)
    draw.line([(px-14,y2),(px+14,y2)], fill=(255,255,255,238), width=5)

    for j, line in enumerate(lines):
        ty = y1 + pad + j*lh + lh//2
        draw.text((cx, ty), line, font=font, fill=(20,20,50,255), anchor="mm")

    return np.array(canvas)


# ═══════════════════════════════════════════════════════════════════
#  Subtitle Overlay — typewriter effect + joke flash
# ═══════════════════════════════════════════════════════════════════

def make_subtitle_array(scene: dict, t: float, W: int, H: int,
                         font=None, joke_font=None) -> np.ndarray:
    canvas = Image.new("RGBA", (W, H), (0,0,0,0))
    draw   = ImageDraw.Draw(canvas)
    bar_h  = 95

    # Slide up from bottom on scene start
    slide = int(bar_h * (1 - ease_out_cubic(min(t / 0.45, 1.0))))

    # Gradient bar
    for row in range(bar_h):
        alpha = int(225 * (1 - (row/bar_h)*0.45))
        ypos  = H - bar_h + row + slide
        if 0 <= ypos < H:
            draw.line([(0,ypos),(W,ypos)], fill=(4,4,22,alpha))

    # Typewriter text
    text = scene.get("narration", "")
    if text and font:
        reveal  = min(t * 2.5, 1.0)
        display = text[:max(1, int(len(text) * reveal))]
        ty      = H - bar_h//2 + slide
        draw_outlined_text(draw, display, (W//2, ty), font,
                            fill=(255,255,255,255), outline=(0,0,0,210), width=2)

    # Joke flash in last 2.5s
    joke = scene.get("joke", "")
    if joke and t > 2.8 and joke_font:
        blink  = int(t * 5) % 2 == 0
        jfill  = (255, 230, 50, 240) if blink else (255, 175, 0, 215)
        draw_outlined_text(draw, f"😂 {joke[:55]}",
                            (W//2, H - bar_h - 48 + slide),
                            joke_font, fill=jfill, outline=(0,0,0,170), width=2)

    return np.array(canvas)


# ═══════════════════════════════════════════════════════════════════
#  Scene Number Badge
# ═══════════════════════════════════════════════════════════════════

def make_badge_array(scene_num: int, total: int, t: float,
                      W: int, H: int, font=None, topic: str = "funny") -> np.ndarray:
    canvas = Image.new("RGBA", (W, H), (0,0,0,0))
    draw   = ImageDraw.Draw(canvas)
    accent = get_accent(topic)

    p = ease_out_cubic(min(t / 0.38, 1.0))
    # Slide in from left
    ox = int(-160 + 70 * p)
    oy = 32; r = 26
    draw.rounded_rectangle([ox, oy, ox+142, oy+r*2], radius=r,
                             fill=(0,0,0,165))
    draw.rounded_rectangle([ox, oy, ox+142, oy+r*2], radius=r,
                             outline=(*accent, 210), width=2)
    if font:
        draw.text((ox+71, oy+r), f"{scene_num}/{total}",
                   font=font, fill=(*accent, 240), anchor="mm")
    return np.array(canvas)


# ═══════════════════════════════════════════════════════════════════
#  Intro Title Card
# ═══════════════════════════════════════════════════════════════════

def make_intro_frame(t: float, title: str, dur: float,
                      W: int, H: int, font_path: str = None,
                      topic: str = "funny") -> np.ndarray:
    c1, c2 = get_bg(topic)
    img    = make_gradient_img(W, H, c1, c2).convert("RGBA")
    draw   = ImageDraw.Draw(img)
    accent = get_accent(topic)
    cx, cy = W//2, H//2

    # Floating particles
    ps    = ParticleSystem(n=22, w=W, h=H, topic=topic, seed=11)
    p_arr = ps.get_frame(t)
    p_img = Image.fromarray(p_arr, "RGBA")
    img.paste(p_img, (0,0), p_img)

    # Glow ring
    for r in range(310, 0, -8):
        a = int(28 * (1-r/310) * (0.65 + 0.35*math.sin(t*2.2)))
        draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(*accent, a))

    # Accent lines
    lp = ease_out_cubic(max(0, min((t-0.38)/0.5, 1.0)))
    lw = int(W*0.38*lp)
    draw.line([(cx-lw,cy-115),(cx+lw,cy-115)], fill=(*accent,180), width=2)
    draw.line([(cx-lw,cy+115),(cx+lw,cy+115)], fill=(*accent,180), width=2)

    # Title zoom-in with bounce
    if t >= 0.2:
        p    = ease_out_bounce(min((t-0.2)/0.88, 1.0))
        size = max(18, int(86*p))
        f    = load_font(font_path, size)
        a    = int(255 * min((t-0.2)*3.5, 1.0))
        # Glow layers
        for gd, ga in [(5,40),(3,60),(1,80)]:
            draw.text((cx,cy), title, font=f, fill=(*accent,ga), anchor="mm")
        draw_outlined_text(draw, title, (cx,cy), f,
                            fill=(255,255,255,a), outline=(0,0,0,a//2), width=3)

    # Sub hint
    if t >= 0.95:
        p = ease_out_cubic(min((t-0.95)/0.5, 1.0))
        sf = load_font(font_path, 40)
        draw.text((cx, cy+90), "দেখতে থাকুন ▼",
                   font=sf, fill=(*accent, int(210*p)), anchor="mm")

    # Fade to black at end
    if t > dur - 0.55:
        fa = int(255 * min((t-(dur-0.55))/0.55, 1.0))
        ov = Image.new("RGBA",(W,H),(0,0,0,fa))
        img.paste(ov,(0,0),ov)

    return np.array(img.convert("RGB"))


# ═══════════════════════════════════════════════════════════════════
#  Outro Card — Subscribe animation
# ═══════════════════════════════════════════════════════════════════

def make_outro_frame(t: float, dur: float,
                      W: int, H: int, font_path: str = None,
                      topic: str = "funny") -> np.ndarray:
    c1, c2 = get_bg(topic)
    img    = make_gradient_img(W, H, c1, c2).convert("RGBA")
    draw   = ImageDraw.Draw(img)
    accent = get_accent(topic)
    cx, cy = W//2, H//2

    # Fade in
    if t < 0.5:
        ov = Image.new("RGBA",(W,H),(0,0,0,int(255*(1-t/0.5))))
        img.paste(ov,(0,0),ov)

    # Subscribe button with pulse glow
    if t >= 0.28:
        p  = ease_out_bounce(min((t-0.28)/0.75, 1.0))
        bw = int(430*p); bh_b = int(74*p)
        bx1 = cx-bw//2; by1 = cy-bh_b//2-55
        bx2 = cx+bw//2; by2 = cy+bh_b//2-55
        pulse = 0.5 + 0.5*math.sin(t*4.5)
        for gi in range(22, 0, -4):
            draw.rounded_rectangle([bx1-gi,by1-gi,bx2+gi,by2+gi],
                                     radius=bh_b//2+gi,
                                     fill=(215, 0, 0, int(55*pulse)))
        draw.rounded_rectangle([bx1,by1,bx2,by2],
                                 radius=bh_b//2, fill=(215,20,20,245))
        bf = load_font(font_path, max(10, int(38*p)))
        draw_outlined_text(draw, "▶  Subscribe করুন",
                            (cx, cy-55), bf,
                            fill=(255,255,255,235), outline=(100,0,0,180), width=2)

    # Like / Bell / Share
    if t >= 0.82:
        p  = ease_out_cubic(min((t-0.82)/0.45, 1.0))
        a  = int(255*p)
        lf = load_font(font_path, 52)
        sf = load_font(font_path, 36)
        draw_outlined_text(draw, "👍 Like  🔔 Bell  📤 Share",
                            (cx,cy+45), lf, fill=(255,255,255,a), outline=(0,0,0,180), width=2)
        draw_outlined_text(draw, "পরবর্তী ভিডিওতে আবার দেখা হবে!",
                            (cx,cy+115), sf, fill=(*accent,a), outline=(0,0,0,150), width=2)

    # Particles
    ps    = ParticleSystem(n=18,w=W,h=H,topic=topic,seed=99)
    p_arr = ps.get_frame(t)
    p_img = Image.fromarray(p_arr,"RGBA")
    img.paste(p_img,(0,0),p_img)

    return np.array(img.convert("RGB"))


# ═══════════════════════════════════════════════════════════════════
#  Flash Transition
# ═══════════════════════════════════════════════════════════════════

def make_flash_array(t: float, dur: float, W: int, H: int,
                      color=(255,255,255)) -> np.ndarray:
    mid = dur / 2
    if t < mid:
        a = int(185 * ease_out_cubic(t / mid))
    else:
        a = int(185 * (1 - ease_out_cubic((t-mid)/mid)))
    return np.array(Image.new("RGBA",(W,H),(*color,a)))
