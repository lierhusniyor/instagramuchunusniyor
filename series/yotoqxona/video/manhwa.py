"""Manhwa (vertikal panel) uslubidagi animatsiya vositalari: panellar, kadr silkinishi, tezlik chiziqlari,
rivoyat qutilari, nutq pufaklari, SFX matnlari, vinyetka, halftone va grain."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

@lru_cache(None)
def F(sz): return ImageFont.truetype(FB, sz)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_io(t): t = clamp(t); return t * t * (3 - 2 * t)

# ---------- rasmlar ----------
EYE_BOX = {"default": (0.04, 0.28, 0.96, 0.58), "jahongir": (0.04, 0.20, 0.96, 0.52)}

def grade(im, sat=0.78, bright=0.86, tint=(-6, -2, 14)):
    a = im.getchannel("A")
    rgb = ImageEnhance.Brightness(ImageEnhance.Color(im.convert("RGB")).enhance(sat)).enhance(bright)
    arr = np.clip(np.asarray(rgb).astype(np.int16) + np.array(tint), 0, 255).astype("uint8")
    out = Image.fromarray(arr).convert("RGBA"); out.putalpha(a); return out

@lru_cache(None)
def face(name, eyes=False):
    im = Image.open(f"assets/{name}.png").convert("RGBA")
    if eyes:
        w, h = im.size
        key = "jahongir" if name.startswith("jahongir") else "default"
        b = EYE_BOX[key]
        im = im.crop((int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)))
    return grade(im)

@lru_cache(None)
def gradient(w, h, c1, c2):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(c1) * (1 - t) + np.array(c2) * t) * np.ones((h, w, 3))
    return Image.fromarray(arr.astype("uint8")).convert("RGBA")

def cover(im, w, h, zoom, focus, shake=(0, 0)):
    sc = max(w / im.width, h / im.height) * zoom
    s = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    ox = int(w / 2 - focus[0] * s.width + shake[0]); oy = int(h / 2 - focus[1] * s.height + shake[1])
    return s, ox, oy

def face_panel(name, w, h, t, dur, z0=1.0, z1=1.12, focus=(0.5, 0.45), bg=((14, 16, 32), (40, 34, 60)),
               eyes=False, shake=0.0, lines=None):
    base = gradient(w, h, *bg).copy()
    k = clamp(t / dur)
    zoom = z0 + (z1 - z0) * ease_io(k)
    sh = (random.uniform(-1, 1) * shake, random.uniform(-1, 1) * shake) if shake > 0.1 else (0, 0)
    s, ox, oy = cover(face(name, eyes), w, h, zoom, focus, sh)
    base.paste(s, (ox, oy), s)
    if lines: speed_lines(base, lines[0], lines[1], t, color=lines[2] if len(lines) > 2 else (255, 255, 255))
    return base

def speed_lines(img, cx_f, cy_f, t, color=(255, 255, 255), n=70, inner=0.36):
    w, h = img.size; rng = random.Random(int(t * 14))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    cx, cy = w * cx_f, h * cy_f; R = math.hypot(w, h)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); spread = rng.uniform(0.006, 0.02)
        r0 = R * rng.uniform(inner, inner + 0.12)
        p = [(cx + math.cos(a) * R, cy + math.sin(a) * R),
             (cx + math.cos(a - spread) * r0, cy + math.sin(a - spread) * r0),
             (cx + math.cos(a + spread) * r0, cy + math.sin(a + spread) * r0)]
        d.polygon(p, fill=color + (rng.randint(110, 215),))
    img.alpha_composite(ov)

# ---------- panel kompozitsiyasi ----------
def paste_panel(canvas, content, rect, skew=0):
    x, y, w, h = rect
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(skew, 0), (w, 0), (w - skew, h), (0, h)], fill=255)
    canvas.paste(content.convert("RGB"), (x, y), m)

# ---------- matn elementlari ----------
def text_wh(d, lines, font, lh):
    return max(d.textlength(l, font=font) for l in lines), lh * len(lines)

def narration(img, text, x, y, t, t0, size=40, color=(255, 255, 255), speed=38, boxcol=(6, 6, 10)):
    """Rivoyat qutisi: qora quti, oq matn, yozuv mashinkasi effekti."""
    if t < t0: return
    d = ImageDraw.Draw(img, "RGBA"); lines = text.split("\n"); f = F(size); lh = int(size * 1.35)
    tw, th = text_wh(d, lines, f, lh)
    bw, bh = int(tw + 44), int(th + 28)
    fade = clamp((t - t0) / 0.18)
    ov = Image.new("RGBA", (bw + 8, bh + 8), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rectangle((0, 0, bw, bh), fill=boxcol + (int(232 * fade),), outline=(235, 235, 235, int(255 * fade)), width=3)
    n = int((t - t0) * speed); shown = text[:n]; yy = 14
    for ln in shown.split("\n"):
        od.text((22, yy), ln, font=f, fill=color + (255,)); yy += lh
    img.alpha_composite(ov, (int(x), int(y)))

def bubble(img, text, cx, cy, t, t0, tail=(-70, 120), size=54, thought=False, who=None):
    if t < t0: return
    k = ease_out_back((t - t0) / 0.28)
    if k < 0.05: return
    d0 = ImageDraw.Draw(img); lines = text.split("\n"); f = F(size); lh = int(size * 1.3)
    tw, th = text_wh(d0, lines, f, lh)
    bw, bh = int(tw + 80), int(th + 60); pad = 160
    ov = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    ox, oy = pad, pad
    if thought:
        d.ellipse((ox, oy, ox + bw, oy + bh), fill=(245, 245, 250, 255), outline=(10, 10, 14, 255), width=6)
        for i, (r, f_) in enumerate([(16, .55), (11, .8), (7, 1.0)]):
            px = ox + bw / 2 + tail[0] * f_ * 0.9; py = oy + bh + (tail[1] - bh / 2) * f_ * 0.9
            d.ellipse((px - r, py - r, px + r, py + r), fill=(245, 245, 250, 255), outline=(10, 10, 14, 255), width=4)
    else:
        d.rounded_rectangle((ox, oy, ox + bw, oy + bh), 36, fill=(250, 250, 252, 255), outline=(10, 10, 14, 255), width=6)
        bx, by = ox + bw / 2, oy + bh / 2
        tx, ty = bx + tail[0], by + tail[1]
        sgn = 1 if tail[1] > 0 else -1
        edge = oy + bh if sgn > 0 else oy
        d.polygon([(bx - 34, edge - sgn * 6), (bx + 34, edge - sgn * 6), (tx, ty)], fill=(250, 250, 252, 255), outline=(10, 10, 14, 255))
        d.line([(bx - 30, edge - sgn * 3), (bx + 30, edge - sgn * 3)], fill=(250, 250, 252, 255), width=8)
    yy = oy + 30
    for ln in lines:
        d.text((ox + bw / 2, yy + lh / 2 - 4), ln, font=f, fill=(12, 12, 16, 255), anchor="mm"); yy += lh
    s = ov.resize((max(1, int(ov.width * k)), max(1, int(ov.height * k))), Image.LANCZOS)
    img.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))

def sfx(img, text, cx, cy, t, t0, size=220, rot=-8, fill=(232, 36, 48), stroke=(8, 6, 10), dur=1.6, shake=8):
    """Manhwa tovush matni (onomatopeya): katta, qiya, qalin chetli."""
    if t < t0 or t > t0 + dur: return
    u = t - t0; k = ease_out_back(u / 0.12) * (1 + 0.04 * math.sin(u * 30))
    fade = clamp((dur - u) / 0.25)
    f = F(size); tmp = Image.new("RGBA", (int(len(text) * size * .78) + 120, size + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    d.text((tmp.width / 2, tmp.height / 2), text, font=f, fill=fill + (255,), anchor="mm", stroke_width=14, stroke_fill=stroke + (255,))
    tmp = tmp.transform(tmp.size, Image.AFFINE, (1, 0.22, -tmp.height * .11, 0, 1, 0), Image.BICUBIC)
    tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC)
    tmp = tmp.resize((max(1, int(tmp.width * k)), max(1, int(tmp.height * k))), Image.LANCZOS)
    if fade < 1: tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * fade)))
    jx = random.uniform(-shake, shake) * (1 if u < 0.5 else 0.3); jy = random.uniform(-shake, shake) * (1 if u < 0.5 else 0.3)
    img.alpha_composite(tmp, (int(cx - tmp.width / 2 + jx), int(cy - tmp.height / 2 + jy)))

# ---------- global effektlar ----------
@lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W * .62)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    return (1 - 0.55 * np.clip(r - 0.45, 0, 1) ** 1.3)[:, :, None].astype("float32")

@lru_cache(None)
def halftone():
    y, x = np.mgrid[0:H, 0:W]; step = 16
    dx = (x % step) - step / 2; dy = (y % step) - step / 2
    rad = step * 0.5 * np.clip((y / H) * 1.1 - 0.35, 0, 1) * 1.0   # pastga qarab qalinlashadi
    return ((dx * dx + dy * dy) < rad * rad).astype("float32")[:, :, None]

_rng = np.random.default_rng(3)
def finish(img, shake=(0, 0), flash=0.0, tint=None):
    if shake != (0, 0):
        img = img.transform(img.size, Image.AFFINE, (1, 0, -shake[0], 0, 1, -shake[1]), Image.BILINEAR)
    a = np.asarray(img.convert("RGB")).astype("float32")
    a *= vignette()
    a *= (1 - 0.22 * halftone())
    n = _rng.integers(0, 255, (H // 4, W // 4), dtype="uint8")
    noise = np.asarray(Image.fromarray(n).resize((W, H), Image.NEAREST)).astype("float32")[:, :, None]
    a += (noise - 127) * 0.09
    if tint is not None: a = a * (1 - tint[3]) + np.array(tint[:3], dtype="float32") * tint[3]
    if flash > 0: a = a * (1 - flash) + 255 * flash
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))

def header(img, ep_text="YOTOQXONA  ·  2-QISM"):
    d = ImageDraw.Draw(img); d.text((W / 2, 34), ep_text, font=F(28), fill=(200, 200, 210, 255), anchor="mm")
