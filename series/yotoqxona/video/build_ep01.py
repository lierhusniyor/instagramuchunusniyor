"""YOTOQXONA 1-qism 'Tanishuv': 15 soniyalik vertikal harakatli komiks (kod bilan)."""
import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
A = "assets"
OUT = sys.argv[1] if len(sys.argv) > 1 else "ep01_tanishuv.mp4"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_sub = ImageFont.truetype(FONT, 84)
f_small = ImageFont.truetype(FONT, 38)
f_note = ImageFont.truetype(FONT, 34)

# (rasm, davomiylik, subtitr)
SCENES = [
    ("body",  4.0, "Men Jahongir.\n22 yoshdaman."),
    ("tired", 4.0, "Ish yo'q.\nPul yo'q."),
    ("smirk", 4.0, "Lekin rejam bor."),
    ("happy", 3.0, "Hammasi keyingi oyda yaxshi bo'ladi."),
]
CTA = "Saqla — 2-qismda xonadoshlar bilan tanishasiz"

def ease_out_back(t):
    t = min(max(t, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def load(name, width):
    im = Image.open(f"{A}/{name}.png").convert("RGBA")
    h = int(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS)

SPRITE = {"body": load("body", 900), "tired": load("tired", 960), "smirk": load("smirk", 960), "happy": load("happy", 960)}

def gradient(c1, c2):
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(c1) * (1 - t) + np.array(c2) * t) * np.ones((H, W, 3))
    return Image.fromarray(arr.astype("uint8")).convert("RGBA")

BG = [gradient((38, 28, 60), (96, 58, 72)), gradient((30, 30, 52), (70, 50, 70)),
      gradient((52, 36, 70), (120, 74, 70)), gradient((70, 40, 80), (160, 100, 70))]

# gulchambar (chiroqlar) uchun yorug' nuqta
glow = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r in range(60, 0, -2):
    gd.ellipse((60 - r, 60 - r, 60 + r, 60 + r), fill=(255, 200, 90, int(120 * (1 - r / 60) ** 2)))
glow = glow.filter(ImageFilter.GaussianBlur(2))
BULBS = [(x, 120 + 60 * math.sin(x / 170 * math.pi) ** 2) for x in range(40, W, 110)]

def draw_lights(img, t):
    d = ImageDraw.Draw(img)
    d.line([(x, y - 18) for x, y in BULBS], fill=(20, 16, 24, 255), width=4)
    for i, (x, y) in enumerate(BULBS):
        k = 0.75 + 0.25 * math.sin(t * 3 + i * 1.7)
        g = glow.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * k)))
        img.alpha_composite(g, (int(x - 60), int(y - 40)))
        d.ellipse((x - 9, y - 6, x + 9, y + 16), fill=(255, int(215 * k + 30), 130, 255))

NOTES = [(60, 560, -8, (255, 226, 90)), (330, 640, 6, (255, 150, 190)), (610, 540, -5, (140, 230, 160)),
         (830, 650, 9, (130, 200, 255)), (170, 800, 7, (255, 190, 120)), (770, 830, -7, (255, 226, 90))]

def draw_notes(img, t):
    for i, (x, y, rot, col) in enumerate(NOTES):
        s = min(max((t - 0.15 * i) / 0.3, 0), 1)
        if s <= 0: continue
        n = Image.new("RGBA", (220, 220), col + (255,))
        d = ImageDraw.Draw(n)
        d.text((110, 110), "keyingi\noyda", font=f_note, fill=(60, 40, 30, 255), anchor="mm", align="center")
        sc = ease_out_back(s)
        n = n.resize((max(1, int(220 * sc)),) * 2).rotate(rot, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(n, (x, y))

def draw_wallet(img, t):
    w = Image.new("RGBA", (560, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(w)
    d.rounded_rectangle((0, 40, 560, 360), 40, fill=(122, 74, 37, 255), outline=(30, 18, 10, 255), width=6)
    d.rounded_rectangle((20, 0, 540, 150), 30, fill=(58, 34, 16, 255), outline=(30, 18, 10, 255), width=6)
    d.line((40, 330, 520, 330), fill=(180, 130, 80, 255), width=4)
    img.alpha_composite(w, (260, 1560))

def draw_moth(img, t, t0=1.0):
    if t < t0: return
    u = t - t0
    x = 800 + 150 * math.sin(u * 1.8) + 90 * u; y = 1640 - 420 * u + 40 * math.sin(u * 7)
    if y < 380: y = 380 + 20 * math.sin(u * 5)
    flap = abs(math.sin(u * 22))
    m = Image.new("RGBA", (200, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    ww = int(40 + 50 * flap)
    d.ellipse((100 - ww - 6, 30, 100 - 4, 100), fill=(190, 170, 140, 255), outline=(60, 50, 40, 255), width=3)
    d.ellipse((104, 30, 100 + ww + 6, 100), fill=(190, 170, 140, 255), outline=(60, 50, 40, 255), width=3)
    d.ellipse((92, 40, 108, 115), fill=(70, 55, 45, 255))
    img.alpha_composite(m, (int(x - 100), int(y - 70)))

def wrap(d, text, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            test = (cur + " " + word).strip()
            if d.textlength(test, font=f_sub) <= maxw: cur = test
            else: lines.append(cur); cur = word
        lines.append(cur)
    return lines

def draw_sub(img, text, st, cta=False):
    k = ease_out_back(st / 0.25)
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, 940)
    lh = 104; y0 = 330 - (len(lines) - 1) * lh / 2
    layer = Image.new("RGBA", (W, 560), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        ld.text((W / 2, 280 + (i - (len(lines) - 1) / 2) * lh), ln, font=f_sub, fill=(255, 255, 255, 255),
                anchor="mm", stroke_width=9, stroke_fill=(15, 10, 20, 255))
    s = 0.6 + 0.4 * k
    layer = layer.resize((int(W * s), int(560 * s)), Image.LANCZOS)
    img.alpha_composite(layer, (int((W - layer.width) / 2), int(380 - layer.height / 2 + 0)))
    if cta:
        d.rounded_rectangle((70, 1740, 1010, 1850), 40, fill=(255, 214, 10, 255))
        d.text((W / 2, 1795), CTA, font=ImageFont.truetype(FONT, 33), fill=(25, 15, 30, 255), anchor="mm")

def frame(scene, t, total_t):
    name, dur, text = SCENES[scene]
    img = BG[scene].copy()
    draw_lights(img, total_t)
    if scene == 2: draw_notes(img, t)
    sp = SPRITE[name]
    pop = ease_out_back(t / 0.35)
    zoom = (0.92 + 0.08 * pop) * (1 + 0.025 * t / dur) * (1 + 0.008 * math.sin(total_t * 3))
    if scene == 3: zoom *= 1 + 0.03 * abs(math.sin(t * 6)) * max(0, 1 - t / 2)
    s = sp.resize((int(sp.width * zoom), int(sp.height * zoom)), Image.LANCZOS)
    rock = 14 * math.sin(total_t * 2.2) if scene == 0 else 0
    x = int((W - s.width) / 2 + rock)
    y = H - s.height + (40 if scene else 90) + int((1 - min(t / 0.35, 1)) * 120)
    img.alpha_composite(s, (x, y))
    if scene == 1:
        draw_wallet(img, t); draw_moth(img, t)
    draw_sub(img, text, t, cta=(scene == 3 and t > dur - 1.6))
    d = ImageDraw.Draw(img)
    d.text((W / 2, 52), "YOTOQXONA · 1-qism", font=f_small, fill=(255, 255, 255, 200), anchor="mm")
    return img.convert("RGB")

def main():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = 0.0
    for si, (_, dur, _) in enumerate(SCENES):
        for fi in range(int(dur * FPS)):
            p.stdin.write(frame(si, fi / FPS, total).tobytes()); total += 1 / FPS
    p.stdin.close(); p.wait()
    print("tayyor:", OUT)

if __name__ == "__main__":
    main()
