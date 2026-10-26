"""YOTOQXONA 2-qism, manhwa uslubida (24 soniya, 6 sahna). Ishlatish: python3 build_manhwa_ep02.py [sahna_raqami|all]"""
import math, random, subprocess, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, ".")
from manhwa import *

DUR = 4.0
NIGHT = ((8, 10, 24), (30, 28, 56))
RED = ((22, 8, 14), (66, 20, 30))
DARK = ((10, 10, 16), (34, 30, 46))
PINK = ((26, 12, 30), (70, 34, 66))

# ---------- protsedur panellar ----------
_rb = random.Random(5)
BUILD = [(x, _rb.randint(180, 620), _rb.randint(110, 210)) for x in range(-40, 1200, 150)]
def skyline_panel(w, h, t):
    img = gradient(w, h, (10, 14, 34), (46, 36, 66)).copy(); d = ImageDraw.Draw(img)
    off = int(t * 14)
    for i, (x, bh, bw) in enumerate(BUILD):
        x0 = x - off % 150; top = h - bh
        d.rectangle((x0, top, x0 + bw, h), fill=(8, 8, 16, 255))
        r = random.Random(i)
        for wy in range(top + 20, h - 20, 44):
            for wx in range(x0 + 14, x0 + bw - 20, 36):
                if r.random() < 0.38: d.rectangle((wx, wy, wx + 16, wy + 22), fill=(255, 205, 110, 230))
    d.ellipse((780, 60, 900, 180), fill=(226, 230, 255, 255))
    return img

def clock_panel(w, h, t):
    img = gradient(w, h, (24, 6, 10), (70, 14, 22)).copy(); d = ImageDraw.Draw(img)
    cx, cy, R = w // 2, h // 2 + 20, 330
    d.ellipse((cx - R - 16, cy - R - 16, cx + R + 16, cy + R + 16), fill=(10, 8, 12, 255), outline=(220, 220, 225, 255), width=8)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(236, 232, 224, 255))
    for i in range(60):
        a = i * math.pi / 30; r1 = R - (34 if i % 5 == 0 else 16)
        d.line([(cx + math.sin(a) * r1, cy - math.cos(a) * r1), (cx + math.sin(a) * (R - 6), cy - math.cos(a) * (R - 6))], fill=(20, 18, 22, 255), width=8 if i % 5 == 0 else 3)
    def hand(a, l, wd, col):
        d.line([(cx, cy), (cx + math.sin(a) * l, cy - math.cos(a) * l)], fill=col, width=wd)
    hand(math.radians(2 * 30 + 17 * 0.5), R * 0.5, 18, (20, 18, 22, 255))
    hand(math.radians(17 * 6), R * 0.78, 12, (20, 18, 22, 255))
    sec = (int(t * 2) % 60)
    jit = 3 * math.sin(((t * 2) % 1) * 20) * (1 - ((t * 2) % 1))
    hand(math.radians(sec * 6 + jit), R * 0.86, 6, (214, 30, 40, 255))
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(214, 30, 40, 255))
    return img

def phone_panel(w, h, t):
    img = gradient(w, h, (10, 12, 26), (34, 30, 56)).copy()
    pw, ph = 560, 980; px, py = (w - pw) // 2, (h - ph) // 2
    jit = int(4 * math.sin(t * 50)) if (0.15 < t < 0.9) else 0
    ph_img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(ph_img)
    d.rounded_rectangle((0, 0, pw, ph), 60, fill=(12, 12, 18, 255), outline=(190, 190, 205, 255), width=7)
    d.rounded_rectangle((22, 22, pw - 22, ph - 22), 44, fill=(18, 24, 40, 255))
    d.text((pw / 2, 170), "HISOB", font=F(44), fill=(130, 150, 190, 255), anchor="mm")
    glow = int(150 + 80 * math.sin(t * 6))
    d.text((pw / 2, 420), "12 000", font=F(130), fill=(90, 235, 150, 255), anchor="mm")
    d.text((pw / 2, 530), "so'm", font=F(56), fill=(190, 200, 225, 255), anchor="mm")
    d.rounded_rectangle((70, 650, pw - 70, 760), 28, fill=(120, 30, 40, 255))
    d.text((pw / 2, 705), "IJARA: -1 800 000", font=F(40), fill=(255, 235, 235, 255), anchor="mm")
    img.alpha_composite(ph_img, (px + jit, py))
    return img

# ---------- sahnalar ----------
def S1(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, skyline_panel(1080, 520, t), (0, 70, 1080, 520))
    paste_panel(img, face_panel("jahongir_tired", 1080, 1250, t, DUR, 1.0, 1.14, (0.5, 0.42), NIGHT), (0, 610, 1080, 1250), 44)
    header(img)
    narration(img, "Yotoqxona.\nTun, 02:17.", 40, 110, t, 0.3)
    narration(img, "Jahongir ikki oydan beri\nish topa olmayotgan edi.", 40, 1640, t, 1.7)
    return img, dict(tint=(6, 10, 30, 0.12))

def S2(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, face_panel("malika_angry", 1080, 820, t, DUR, 1.02, 1.16, (0.5, 0.40), RED, shake=14 if t < 0.5 else 2, lines=(0.5, 0.45)), (0, 70, 1080, 820), 50)
    paste_panel(img, face_panel("malika_angry", 1080, 440, t, DUR, 1.0, 1.08, (0.5, 0.5), DARK, eyes=True), (0, 910, 1080, 440), 50)
    paste_panel(img, gradient(1080, 500, (8, 8, 14), (26, 22, 36)), (0, 1370, 1080, 500), 0)
    header(img)
    sfx(img, "DAN!", 600, 330, t, 0.05, size=260, rot=-9)
    narration(img, "U kirdi.\nVa xona sovub ketdi.", 40, 940, t, 1.0)
    bubble(img, "Ijara.\nUch kun qoldi.", 540, 1620, t, 2.0, tail=(-200, -150))
    return img, dict(flash=max(0, 0.85 - t * 7), shake=((random.uniform(-14, 14), random.uniform(-14, 14)) if t < 0.4 else (0, 0)), tint=(30, 4, 8, 0.10))

def S3(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, clock_panel(1080, 860, t), (0, 70, 1080, 860))
    paste_panel(img, face_panel("jahongir_shock", 1080, 470, t, DUR, 1.0, 1.1, (0.5, 0.5), RED, eyes=True, shake=3 + 3 * t), (0, 950, 1080, 470), 44)
    paste_panel(img, gradient(1080, 430, (14, 6, 10), (34, 10, 16)), (0, 1440, 1080, 430), 0)
    header(img)
    n = int(t * 2)
    if n % 2 == 0: sfx(img, "TIK", 230, 330, t, n / 2, size=190, rot=-10, dur=0.5, fill=(240, 240, 245))
    else: sfx(img, "TOK", 850, 640, t, n / 2, size=190, rot=8, dur=0.5, fill=(240, 240, 245))
    narration(img, "72 soat.", 60, 1500, t, 0.4, size=96, color=(255, 90, 100))
    narration(img, "Jahongirning yuragi tezlashdi.", 60, 1740, t, 1.8)
    return img, dict(tint=(40, 4, 10, 0.16))

def S4(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, phone_panel(1080, 840, t), (0, 70, 1080, 840))
    paste_panel(img, face_panel("dilnoza_sad", 1080, 930, t, DUR, 1.0, 1.12, (0.5, 0.46), PINK), (0, 930, 1080, 930), 44)
    header(img)
    narration(img, "Dilnoza telefonini ochdi.", 40, 100, t, 0.2)
    sfx(img, "BZZT", 800, 270, t, 0.15, size=150, rot=7, dur=0.9)
    bubble(img, "Hisobimda 12 ming...\nBu — belgimi?", 560, 1560, t, 1.6, tail=(-60, -170), thought=True)
    return img, dict(tint=(30, 8, 30, 0.10))

def S5(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, face_panel("malika_smirk", 1080, 820, t, DUR, 1.0, 1.12, (0.5, 0.42), DARK), (0, 70, 1080, 820), 60)
    paste_panel(img, face_panel("dilnoza_shock", 530, 960, t, DUR, 1.0, 1.1, (0.5, 0.5), PINK, shake=2), (0, 910, 530, 960), 30)
    paste_panel(img, face_panel("jahongir_shock", 530, 960, t, DUR, 1.0, 1.1, (0.5, 0.5), NIGHT, shake=2), (550, 910, 530, 960), 30)
    header(img)
    narration(img, "Uch xonadosh.\nUch kun.", 40, 100, t, 0.2)
    bubble(img, "Birimiz topishimiz kerak.\nHozir.", 620, 760, t, 1.2, tail=(-120, 120))
    sfx(img, "...", 540, 1380, t, 2.6, size=180, rot=0, dur=1.2, fill=(240, 240, 245))
    return img, dict(tint=(8, 8, 24, 0.10))

def S6(t, f):
    img = Image.new("RGBA", (W, H), (4, 4, 8, 255))
    paste_panel(img, face_panel("jahongir_smirk", 1080, 1500, t, DUR, 1.0, 1.15, (0.5, 0.40), NIGHT, lines=(0.5, 0.4, (255, 255, 255)) if t < 0.5 else None, shake=10 if t < 0.35 else 0), (0, 70, 1080, 1500), 40)
    header(img)
    bubble(img, "Menda reja bor.", 540, 1180, t, 0.9, tail=(-30, -150))
    narration(img, "(Aslida... yo'q edi.)", 40, 1360, t, 2.0, color=(255, 90, 100), size=44)
    if t > 2.6:
        k = ease_out_back((t - 2.6) / 0.3)
        d = ImageDraw.Draw(img); h = int(210 * k)
        d.rectangle((0, 1640, W, 1640 + h), fill=(190, 20, 34, 255))
        if k > 0.7:
            d.text((W / 2, 1700), "3-QISM  ·  ERTAGA", font=F(76), fill=(255, 255, 255, 255), anchor="mm")
            d.text((W / 2, 1782), "Saqla va do'stingga yubor", font=F(38), fill=(255, 220, 220, 255), anchor="mm")
    return img, dict(flash=max(0, 0.9 - t * 8), shake=((random.uniform(-10, 10), random.uniform(-10, 10)) if t < 0.3 else (0, 0)))

SCENES = [S1, S2, S3, S4, S5, S6]

def render(idx, out):
    random.seed(idx)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "veryfast", out], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        img, fx = SCENES[idx](t, fi)
        fade = clamp(t / 0.12)
        frame = finish(img, shake=fx.get("shake", (0, 0)), flash=fx.get("flash", 0.0), tint=fx.get("tint"))
        if fade < 1: frame = Image.blend(Image.new("RGB", frame.size, (0, 0, 0)), frame, fade)
        p.stdin.write(frame.tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs("tmp_m", exist_ok=True)
    if arg != "all":
        render(int(arg), f"tmp_m/s{arg}.mp4"); sys.exit()
    procs = []
    for i in range(6):
        procs.append(subprocess.Popen([sys.executable, "build_manhwa_ep02.py", str(i)]))
        if len(procs) % 2 == 0:
            for q in procs[-2:]: q.wait()
    for q in procs: q.wait()
    with open("tmp_m/list.txt", "w") as fh:
        for i in range(6): fh.write(f"file 's{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "tmp_m/list.txt", "-c", "copy", "ep02_manhwa_silent.mp4"], check=True)
    print("tayyor: ep02_manhwa_silent.mp4")
