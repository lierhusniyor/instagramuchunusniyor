"""YOTOQXONA 2-qism 'Xonadoshlar': 20 soniya, Malika + Dilnoza + Jahongir."""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "."); import build_ep01 as B

W, H, FPS = B.W, B.H, B.FPS
OUT = sys.argv[1] if len(sys.argv) > 1 else "ep02_xonadoshlar.mp4"
FONT = B.FONT
f_tag = ImageFont.truetype(FONT, 46)
f_prop = ImageFont.truetype(FONT, 64)
f_prop2 = ImageFont.truetype(FONT, 40)
f_cta = ImageFont.truetype(FONT, 33)

# (yuz, davomiylik, subtitr, ism, ism rangi, fon (yuqori, past), rekvizit)
SCENES = [
    ("malika_angry",  4.0, "Bu Malika.\nIjarani u yig'adi.", "MALIKA", (110, 170, 230), ((24, 34, 66), (62, 70, 110)), None),
    ("malika_shock",  4.0, "Ijara 3 kundan keyin!", "MALIKA", (110, 170, 230), ((40, 28, 60), (110, 60, 80)), "rent"),
    ("dilnoza_happy", 4.0, "Bu Dilnoza.\nHamma narsada\n\"belgi\" ko'radi.", "DILNOZA", (255, 150, 195), ((70, 34, 76), (150, 80, 110)), None),
    ("dilnoza_shock", 4.0, "Hisobimda 12 ming.\nBu belgimi?", "DILNOZA", (255, 150, 195), ((52, 30, 70), (130, 70, 100)), "balance"),
    ("jahongir_smirk", 4.0, "Menda reja bor:\nkeyingi oyda.", "JAHONGIR", (255, 214, 10), ((60, 40, 70), (150, 100, 70)), None),
]
CTA = "Saqla — 3-qism ertaga"

def gradient(c1, c2): return B.gradient(c1, c2)
BGS = [gradient(s[5][0], s[5][1]) for s in SCENES]

def load(name, height):
    im = Image.open(f"assets/{name}.png").convert("RGBA")
    return im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
SPR = {s[0]: load(s[0], 1000) for s in SCENES}

def prop_rent(img, t):
    k = B.ease_out_back((t - 0.3) / 0.35)
    if k <= 0.06: return
    p = Image.new("RGBA", (620, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, 620, 330), 26, fill=(250, 246, 236, 255), outline=(40, 30, 30, 255), width=6)
    d.text((310, 100), "IJARA TO'LOVI", font=f_prop2, fill=(60, 40, 40, 255), anchor="mm")
    d.text((310, 205), "3 KUN QOLDI", font=f_prop, fill=(214, 40, 40, 255), anchor="mm")
    d.line((60, 270, 560, 270), fill=(150, 130, 120, 255), width=4)
    p = p.resize((int(620 * k), int(330 * k))).rotate(-5 + 2 * math.sin(t * 5), expand=True, resample=Image.BICUBIC)
    img.alpha_composite(p, (int(W / 2 - p.width / 2), 540))

def prop_balance(img, t):
    k = B.ease_out_back((t - 0.3) / 0.35)
    if k <= 0.06: return
    p = Image.new("RGBA", (640, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, 640, 300), 30, fill=(28, 30, 44, 255), outline=(255, 255, 255, 255), width=5)
    d.text((40, 46), "HISOB", font=f_prop2, fill=(150, 160, 190, 255))
    d.text((320, 160), "12 000", font=ImageFont.truetype(FONT, 110), fill=(120, 240, 160, 255), anchor="mm")
    d.text((600, 262), "so'm", font=f_prop2, fill=(210, 215, 235, 255), anchor="rb")
    p = p.resize((int(640 * k), int(300 * k))).rotate(4 * math.sin(t * 4), expand=True, resample=Image.BICUBIC)
    img.alpha_composite(p, (int(W / 2 - p.width / 2), 540))

def draw_tag(img, name, color, t):
    k = B.ease_out_back((t - 0.1) / 0.3)
    if k <= 0.06: return
    tag = Image.new("RGBA", (460, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(tag)
    d.rounded_rectangle((0, 0, 460, 90), 40, fill=color + (255,), outline=(20, 14, 24, 255), width=5)
    d.text((230, 45), name, font=f_tag, fill=(25, 15, 30, 255), anchor="mm")
    tag = tag.resize((int(460 * k), max(1, int(90 * k))))
    img.alpha_composite(tag, (int(W / 2 - tag.width / 2), 925 - tag.height // 2))

def draw_sub(img, text, t, cta):
    k = B.ease_out_back(t / 0.25)
    d = ImageDraw.Draw(img)
    lines = []
    for para in text.split("\n"):
        lines += B.wrap(d, para, 940)
    lh = 104
    layer = Image.new("RGBA", (W, 560), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        ld.text((W / 2, 280 + (i - (len(lines) - 1) / 2) * lh), ln, font=B.f_sub, fill=(255, 255, 255, 255),
                anchor="mm", stroke_width=9, stroke_fill=(15, 10, 20, 255))
    s = 0.6 + 0.4 * k
    layer = layer.resize((int(W * s), int(560 * s)), Image.LANCZOS)
    img.alpha_composite(layer, (int((W - layer.width) / 2), int(330 - layer.height / 2)))
    if cta:
        d.rounded_rectangle((70, 1760, 1010, 1860), 40, fill=(255, 214, 10, 255))
        d.text((W / 2, 1810), CTA, font=f_cta, fill=(25, 15, 30, 255), anchor="mm")

def frame(si, t, total):
    name, dur, text, who, col, _, prop = SCENES[si]
    img = BGS[si].copy()
    B.draw_lights(img, total)
    sp = SPR[name]
    pop = B.ease_out_back(t / 0.35)
    zoom = (0.9 + 0.1 * pop) * (1 + 0.03 * t / dur) * (1 + 0.008 * math.sin(total * 3))
    if name == "malika_shock" or name == "dilnoza_shock":
        zoom *= 1 + 0.015 * math.sin(t * 40) * max(0, 1 - t / 1.2)   # titrash
    s = sp.resize((int(sp.width * zoom), int(sp.height * zoom)), Image.LANCZOS)
    tilt = 2.2 * math.sin(total * 2.0)
    s = s.rotate(tilt, resample=Image.BICUBIC, expand=True)
    x = int((W - s.width) / 2)
    y = H - s.height + 60 + int((1 - min(t / 0.35, 1)) * 140)
    img.alpha_composite(s, (x, y))
    if prop == "rent": prop_rent(img, t)
    if prop == "balance": prop_balance(img, t)
    draw_tag(img, who, col, t)
    draw_sub(img, text, t, cta=(si == len(SCENES) - 1 and t > dur - 1.8))
    ImageDraw.Draw(img).text((W / 2, 52), "YOTOQXONA · 2-qism", font=B.f_small, fill=(255, 255, 255, 200), anchor="mm")
    return img.convert("RGB")

def main():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = 0.0
    for si, sc in enumerate(SCENES):
        for fi in range(int(sc[1] * FPS)):
            p.stdin.write(frame(si, fi / FPS, total).tobytes()); total += 1 / FPS
    p.stdin.close(); p.wait(); print("tayyor:", OUT)

if __name__ == "__main__":
    main()
