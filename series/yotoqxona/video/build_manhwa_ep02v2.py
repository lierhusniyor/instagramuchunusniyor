"""YOTOQXONA 2-qism (v2): aniq sujet, to'liq bo'yli qahramonlar, manhwa uslubi. 24 s, 6 sahna.
Sujet: ijara 1 800 000, muddat 3 kun -> hisoblar: jami 15 000 -> Jahongir "reja bor" -> eshik: "Ijara BUGUN!"."""
import math, random, subprocess, sys, os
from functools import lru_cache
from PIL import Image, ImageDraw
sys.path.insert(0, ".")
from manhwa import *

DUR = 4.0
NIGHT = ((8, 10, 24), (30, 28, 56)); RED = ((22, 8, 14), (66, 20, 30)); DARK = ((10, 10, 16), (34, 30, 46)); PINK = ((26, 12, 30), (70, 34, 66))

@lru_cache(None)
def sprite(name, h):
    im = grade(Image.open(f"assets/{name}.png").convert("RGBA"), sat=0.9, bright=0.92)
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)

@lru_cache(None)
def room_img(): return Image.open("assets/room_bg.png").convert("RGBA")

def room_panel(w, h, t, chars, z0=1.0, z1=1.08, dim=0.0, rim=None, shake=0.0):
    k = clamp(t / DUR); sh = (random.uniform(-1, 1) * shake, random.uniform(-1, 1) * shake) if shake else (0, 0)
    s, ox, oy = cover(room_img(), w, h, z0 + (z1 - z0) * ease_io(k), (0.5, 0.5), sh)
    base = Image.new("RGBA", (w, h), (0, 0, 0, 255)); base.paste(s, (ox, oy), s)
    for name, fx, ch, dx, dy in chars:
        sp = sprite(name, int(ch * (1 + 0.006 * math.sin(t * 2.2))))
        x = int(fx * w - sp.width / 2 + dx); y = int(h - sp.height - 18 + dy)
        sh_ = Image.new("RGBA", (sp.width, 60), (0, 0, 0, 0)); ImageDraw.Draw(sh_).ellipse((10, 6, sp.width - 10, 54), fill=(0, 0, 0, 150))
        base.alpha_composite(sh_, (x, h - 60 + dy // 2))
        base.paste(sp, (x, y), sp)
    if dim > 0:
        ov = Image.new("RGBA", (w, h), (4, 6, 18, int(255 * dim))); base.alpha_composite(ov)
    if rim:
        g = np.zeros((h, w, 4), dtype="uint8"); ys = np.linspace(0, 1, h)[:, None]
        g[:, :, 0] = rim[0]; g[:, :, 1] = rim[1]; g[:, :, 2] = rim[2]; g[:, :, 3] = (np.clip(ys - 0.55, 0, 1) * 2.2 * rim[3]).astype("uint8")
        base.alpha_composite(Image.fromarray(g, "RGBA"))
    return base

def shout(img, text, cx, cy, t, t0, size=84):
    if t < t0: return
    k = ease_out_back((t - t0) / 0.2)
    if k < 0.05: return
    d0 = ImageDraw.Draw(img); lines = text.split("\n"); f = F(size); lh = int(size * 1.2)
    tw, th = text_wh(d0, lines, f, lh); rx, ry = tw / 2 + 90, th / 2 + 70
    n = 22; pts = []
    rng = random.Random(4)
    for i in range(n * 2):
        a = math.pi * i / n; r = 1.0 if i % 2 == 0 else 0.78 + rng.uniform(-0.04, 0.04)
        pts.append((rx * 1.12 * r * math.cos(a) + rx * 1.2, ry * 1.25 * r * math.sin(a) + ry * 1.3))
    ov = Image.new("RGBA", (int(rx * 2.5), int(ry * 2.7)), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.polygon(pts, fill=(205, 22, 36, 255), outline=(255, 255, 255, 255))
    d.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=7)
    yy = ov.height / 2 - th / 2
    for ln in lines:
        d.text((ov.width / 2, yy + lh / 2), ln, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(30, 0, 6, 255)); yy += lh
    s = ov.resize((max(1, int(ov.width * k)), max(1, int(ov.height * k))), Image.LANCZOS)
    img.alpha_composite(s, (int(cx - s.width / 2 + random.uniform(-4, 4)), int(cy - s.height / 2 + random.uniform(-4, 4))))

def notice_panel(w, h, t):
    img = gradient(w, h, (12, 8, 14), (40, 18, 24)).copy(); d = ImageDraw.Draw(img)
    k = ease_out_back((t - 0.5) / 0.4)
    if k > 0.05:
        pw, ph = 860, 520
        p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(p)
        pd.rounded_rectangle((0, 0, pw, ph), 22, fill=(246, 241, 228, 255), outline=(30, 20, 20, 255), width=6)
        pd.text((pw / 2, 90), "IJARA TO'LOVI", font=F(64), fill=(50, 30, 30, 255), anchor="mm")
        pd.text((pw / 2, 230), "1 800 000", font=F(150), fill=(200, 24, 36, 255), anchor="mm")
        pd.text((pw / 2, 330), "so'm", font=F(56), fill=(60, 40, 40, 255), anchor="mm")
        pd.line((60, 390, pw - 60, 390), fill=(150, 130, 120, 255), width=4)
        pd.text((pw / 2, 455), "MUDDAT:  3 KUN", font=F(66), fill=(50, 30, 30, 255), anchor="mm")
        p = p.resize((max(1, int(pw * k)), max(1, int(ph * k)))).rotate(-3 + 1.5 * math.sin(t * 3), expand=True, resample=Image.BICUBIC)
        img.alpha_composite(p, (int(w / 2 - p.width / 2), int(h / 2 - p.height / 2 - 20)))
    return img

def calc_panel(w, h, t):
    img = gradient(w, h, (8, 10, 18), (24, 22, 38)).copy(); d = ImageDraw.Draw(img)
    rows = [("MALIKA", "3 000", (110, 170, 230), 0.3), ("DILNOZA", "12 000", (255, 150, 195), 0.9), ("JAHONGIR", "0", (255, 214, 10), 1.5)]
    for i, (nm, val, col, t0) in enumerate(rows):
        k = ease_out_back((t - t0) / 0.3)
        if k < 0.05: continue
        y = 130 + i * 150; off = int((1 - clamp(k)) * 400)
        d.rounded_rectangle((60 + off, y - 55, 1020 + off, y + 55), 26, fill=(18, 20, 32, 255), outline=col + (255,), width=4)
        d.text((100 + off, y), nm, font=F(52), fill=col + (255,), anchor="lm")
        d.text((980 + off, y), val + " so'm", font=F(60), fill=(240, 240, 245, 255), anchor="rm")
    if t > 2.1:
        k = ease_out_back((t - 2.1) / 0.3)
        d.line((60, 590, 1020, 590), fill=(220, 220, 230, 255), width=5)
        d.text((100, 650), "JAMI:", font=F(60), fill=(150, 240, 180, 255), anchor="lm")
        d.text((980, 650), "15 000", font=F(int(84 * clamp(k, 0.3, 1.1))), fill=(150, 240, 180, 255), anchor="rm")
    if t > 2.9:
        k = ease_out_back((t - 2.9) / 0.3)
        d.text((100, 760), "KERAK:", font=F(60), fill=(255, 100, 110, 255), anchor="lm")
        d.text((980, 760), "1 800 000", font=F(int(84 * clamp(k, 0.3, 1.1))), fill=(255, 100, 110, 255), anchor="rm")
        d.rounded_rectangle((60, 850, 1020, 910), 28, fill=(40, 12, 18, 255), outline=(255, 255, 255, 255), width=3)
        fill_w = max(10, int(960 * 15000 / 1800000 * clamp(k)))
        d.rounded_rectangle((60, 850, 60 + fill_w + 14, 910), 28, fill=(120, 240, 160, 255))
        d.text((540, 945), "0,8 %", font=F(42), fill=(230, 230, 240, 255), anchor="mm")
    return img

def door_panel(w, h, t, knocks):
    img = gradient(w, h, (6, 6, 10), (14, 10, 14)).copy(); d = ImageDraw.Draw(img)
    dw, dh = 560, h - 40; x0 = (w - dw) // 2
    kn = max([0] + [1 - (t - k0) * 6 for k0 in knocks if 0 <= t - k0 < 0.17])
    jx = int(random.uniform(-9, 9) * kn)
    d.rectangle((x0 + jx, 40, x0 + dw + jx, h), fill=(34, 22, 18, 255), outline=(8, 6, 6, 255), width=8)
    d.rectangle((x0 + 40 + jx, 90, x0 + dw - 40 + jx, 330), outline=(18, 12, 10, 255), width=10)
    d.rectangle((x0 + 40 + jx, 380, x0 + dw - 40 + jx, h - 70), outline=(18, 12, 10, 255), width=10)
    d.ellipse((x0 + dw - 90 + jx, h // 2 - 20, x0 + dw - 56 + jx, h // 2 + 14), fill=(190, 160, 90, 255))
    glow = Image.new("RGBA", (dw, 120), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for i in range(60): gd.rectangle((0, 120 - i * 2, dw, 120), fill=(255, 40, 50, int(4 + i * 0.9)))
    img.alpha_composite(glow, (x0 + jx, h - 120)); d.rectangle((x0 + jx, h - 12, x0 + dw + jx, h), fill=(255, 60, 70, 255))
    return img

# ---------- sahnalar ----------
def S1(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, room_panel(1080, 1080, t, [("full_jahongir", 0.64, 900, 6 * math.sin(t * 1.6), 0)], 1.0, 1.1, dim=0.08), (0, 70, 1080, 1080), 44)
    paste_panel(img, notice_panel(1080, 700, t), (0, 1170, 1080, 700), 0)
    header(img)
    narration(img, "Yotoqxona.\nErtalab, 07:40.", 40, 110, t, 0.3)
    narration(img, "Jahongir hali uxlayotgan edi.\nTelefon... ijara haqida yozdi.", 40, 1180, t, 1.2, size=34)
    return img, dict(tint=(6, 10, 30, 0.10))

def S2(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    slide = (1 - ease_out(t / 0.35)) * -520
    paste_panel(img, room_panel(1080, 1250, t, [("full_jahongir", 0.74, 960, 0, 0), ("full_malika", 0.30, 1060, slide, 0)], 1.0, 1.06, shake=10 if t < 0.5 else 1.5), (0, 70, 1080, 1250), 50)
    paste_panel(img, face_panel("malika_angry", 1080, 530, t, DUR, 1.0, 1.1, (0.5, 0.45), RED), (0, 1340, 1080, 530), 50)
    header(img)
    sfx(img, "DAN!", 700, 330, t, 0.1, size=250, rot=-9)
    narration(img, "Malika kirdi.\nVa xona sovub ketdi.", 40, 130, t, 0.9)
    bubble(img, "Hamma o'z hisobini\nko'rsatsin!", 700, 1480, t, 1.9, tail=(-160, -90))
    return img, dict(flash=max(0, 0.8 - t * 7), shake=((random.uniform(-14, 14), random.uniform(-14, 14)) if t < 0.4 else (0, 0)), tint=(26, 4, 8, 0.08))

def S3(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, room_panel(1080, 1250, t, [("full_malika", 0.76, 960, 0, 0), ("full_dilnoza", 0.32, 1060, 0, 0)], 1.0, 1.07), (0, 70, 1080, 1250), 50)
    paste_panel(img, face_panel("dilnoza_shock", 1080, 530, t, DUR, 1.0, 1.1, (0.5, 0.45), PINK, shake=2), (0, 1340, 1080, 530), 50)
    header(img)
    narration(img, "Dilnoza telefonini ochdi.", 40, 120, t, 0.2)
    sfx(img, "BZZT", 780, 330, t, 0.15, size=150, rot=7, dur=0.9)
    bubble(img, "Menda...\n12 ming.", 700, 1470, t, 1.3, tail=(-190, -100), thought=False)
    return img, dict(tint=(30, 8, 30, 0.08))

def S4(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, calc_panel(1080, 1000, t), (0, 70, 1080, 1000), 0)
    paste_panel(img, room_panel(1080, 780, t, [("full_dilnoza", 0.22, 700, 0, 0), ("full_malika", 0.50, 740, 0, 0), ("full_jahongir", 0.80, 700, 0, 0)], 1.0, 1.05, dim=0.15), (0, 1090, 1080, 780), 44)
    header(img)
    narration(img, "Yetishmaydi: 1 785 000 so'm.", 40, 1120, t, 3.0, color=(255, 100, 110), size=40)
    return img, dict(tint=(8, 8, 24, 0.10))

def S5(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, room_panel(1080, 1330, t, [("full_jahongir", 0.5, 1300, 0, 0)], 1.05, 1.18, dim=0.18, shake=7 if t < 0.35 else 0), (0, 70, 1080, 1330), 40)
    paste_panel(img, face_panel("jahongir_smirk", 1080, 440, t, DUR, 1.0, 1.1, (0.5, 0.5), NIGHT, eyes=True), (0, 1430, 1080, 440), 40)
    header(img)
    bubble(img, "Menda reja bor.", 800, 640, t, 0.8, tail=(-190, -150))
    narration(img, "U bu gapni o'tgan oy ham aytgan edi.", 40, 1350, t, 2.0, color=(255, 100, 110), size=36)
    return img, dict(tint=(6, 8, 26, 0.10))

def S6(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, room_panel(1080, 1150, t, [("full_dilnoza", 0.24, 950, 0, 0), ("full_malika", 0.50, 1010, 0, 0), ("full_jahongir", 0.78, 950, 0, 0)], 1.0, 1.06, dim=0.42, rim=(255, 40, 50, 160), shake=6 if any(0 <= t - k < 0.16 for k in (0.2, 0.9, 1.6)) else 0), (0, 70, 1080, 1150), 40)
    paste_panel(img, door_panel(1080, 630, t, (0.2, 0.9, 1.6)), (0, 1240, 1080, 630), 0)
    header(img)
    for i, k0 in enumerate((0.2, 0.9, 1.6)): sfx(img, "TOK!", 220 + i * 320, 420 + (i % 2) * 60, t, k0, size=170, rot=-8 + i * 7, dur=0.55, fill=(240, 240, 245))
    shout(img, "IJARA —\nBUGUN!", 540, 1500, t, 2.1)
    if t > 2.8:
        k = ease_out_back((t - 2.8) / 0.3); d = ImageDraw.Draw(img); h = int(150 * k)
        d.rectangle((0, 1770, W, 1770 + h), fill=(190, 20, 34, 255))
        if k > 0.7: d.text((W / 2, 1822), "3-QISM  ·  ERTAGA", font=F(64), fill=(255, 255, 255, 255), anchor="mm")
    return img, dict(flash=0.0, tint=(30, 4, 8, 0.10))

SCENES = [S1, S2, S3, S4, S5, S6]

def render(idx, out):
    random.seed(idx)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "veryfast", out], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        img, fx = SCENES[idx](t, fi)
        frame = finish(img, shake=fx.get("shake", (0, 0)), flash=fx.get("flash", 0.0), tint=fx.get("tint"))
        fade = clamp(t / 0.12)
        if fade < 1: frame = Image.blend(Image.new("RGB", frame.size, (0, 0, 0)), frame, fade)
        p.stdin.write(frame.tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs("tmp_v2", exist_ok=True)
    if arg != "all":
        render(int(arg), f"tmp_v2/s{arg}.mp4"); sys.exit()
    procs = []
    for i in range(6):
        procs.append(subprocess.Popen([sys.executable, "build_manhwa_ep02v2.py", str(i)]))
        if len(procs) % 2 == 0:
            for q in procs[-2:]: q.wait()
    for q in procs: q.wait()
    with open("tmp_v2/list.txt", "w") as fh:
        for i in range(6): fh.write(f"file 's{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "tmp_v2/list.txt", "-c", "copy", "ep02v2_silent.mp4"], check=True)
    print("tayyor: ep02v2_silent.mp4")
