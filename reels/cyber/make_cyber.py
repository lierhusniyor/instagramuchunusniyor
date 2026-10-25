#!/usr/bin/env python3
"""Cyberpunk 3D neon ko'cha: bitta uzluksiz "kamera" kadri, kinetik matn, sintez musiqa.

Ishlatish:
    python3 make_cyber.py --dur 15.5 --video chiqish.mp4 --music musiqa.wav
    python3 make_cyber.py --dur 15.5 --preview 1,5,9,14      # PNG kadrlar (sinov)
"""
import argparse
import math
import random
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
F = 900.0            # fokus (piksel)
Z_MIN, Z_MAX = 7.0, 190.0
SLOT = 22.0          # minoralar orasidagi masofa (m)
X_IN = 6.5           # yo'l yarim kengligi (m)
HORIZON = 1000

FONT = next((f for f in (
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if Path(f).exists()),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

CYAN, PINK, YELLOW, VIOLET = (0, 240, 255), (255, 40, 170), (255, 225, 60), (150, 80, 255)
PAL = [CYAN, PINK, YELLOW, VIOLET]
FOG = (255, 70, 150)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease_out_back(t):
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def mix(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ---------------------------------------------------------------- statik qatlamlar
def make_sky():
    h = H + 700
    hy = HORIZON + 350          # sky ichidagi ufq chizig'i
    arr = np.zeros((h, W, 3), np.float32)
    stops = [(0, (6, 2, 28)), (hy * 0.45, (40, 8, 85)), (hy * 0.8, (150, 25, 130)), (hy, (255, 90, 120))]
    ys = np.arange(h)
    for ch in range(3):
        xs = [s[0] for s in stops]
        vs = [s[1][ch] for s in stops]
        arr[:, :, ch] = np.interp(ys, xs, vs)[:, None]
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    for _ in range(260):
        x, y = rnd.randrange(W), rnd.randrange(int(hy * 0.8))
        v = rnd.randrange(120, 255)
        d.point((x, y), fill=(v, v, 255))
    # retro quyosh
    cx, cy, r = W // 2, hy - 230, 300
    for i in range(r, 0, -2):
        t = i / r
        col = mix((255, 240, 90), (255, 30, 150), t ** 1.4)
        d.ellipse((cx - i, cy - i, cx + i, cy + i), fill=col)
    for k in range(9):          # quyosh chiziqlari
        y0 = cy + 20 + k * 30
        d.rectangle((cx - r, y0, cx + r, y0 + 4 + k * 2), fill=lerp_c((255, 90, 120), (60, 10, 110), 0.5))
    return img, hy


def lerp_c(a, b, t):
    return mix(a, b, t)


def make_skyline():
    """Uzoqdagi ufq silueti (quyosh oldida)."""
    wd, hh = W + 400, 620
    img = Image.new("RGBA", (wd, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(11)
    x = 0
    while x < wd:
        bw = rnd.randrange(40, 130)
        bh = rnd.randrange(80, 520)
        col = (28, 8, 62, 255)
        d.rectangle((x, hh - bh, x + bw, hh), fill=col)
        if rnd.random() < 0.4:
            d.rectangle((x + bw // 2 - 2, hh - bh - 60, x + bw // 2 + 2, hh - bh), fill=col)
        for _ in range(bh // 40):
            wx, wy = x + rnd.randrange(4, max(6, bw - 8)), hh - rnd.randrange(10, bh)
            c = rnd.choice(PAL) + (200,)
            d.rectangle((wx, wy, wx + 4, wy + 6), fill=c)
        x += bw + rnd.randrange(0, 14)
    return img


def make_overlays():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip(1.15 - 0.55 * r ** 2, 0.25, 1.0)
    scan = np.where((np.arange(H) % 4) < 1, 0.86, 1.0)[:, None]
    m = (vig * scan)[:, :, None] * np.ones((1, 1, 3), np.float32)
    overlay = Image.fromarray((m * 255).astype(np.uint8))
    grains = [Image.effect_noise((W, H), 38).convert("RGB") for _ in range(4)]
    return overlay, grains


# ---------------------------------------------------------------- matn
BEATS = [  # (boshlanish, tugash, qatorlar) — davomiylikka nisbatan
    (0.00, 0.20, ["INSTAGRAM", "KELAJAGI"]),
    (0.20, 0.38, ["NEON", "SHAHAR"]),
    (0.38, 0.58, ["YANGI", "G'OYALAR"]),
    (0.58, 0.79, ["SEN", "BIRINCHISAN!"]),
    (0.79, 1.00, ["OBUNA BO'L", "@usniy_or"]),
]


def build_text_cache():
    cache = []
    for bi, (_, _, lines) in enumerate(BEATS):
        items = []
        for li, line in enumerate(lines):
            size = 170 if li == 0 else 130
            if len(line) > 9:
                size = int(size * 9 / len(line) * 1.05)
            if bi == 4 and li == 1:
                size = 92
            font = ImageFont.truetype(FONT, size)
            probe = ImageDraw.Draw(Image.new("L", (10, 10)))
            width = probe.textlength(line, font=font)
            if width > 800:
                size = int(size * 800 / width)
                font = ImageFont.truetype(FONT, size)
            tw = int(probe.textlength(line, font=font)) + 60
            th = int(size * 1.5)
            col = PAL[(bi + li) % len(PAL)] if li else (255, 255, 255)
            glow_col = PAL[(bi * 2 + li) % len(PAL)]
            if bi == 4 and li == 1:
                col, glow_col = (255, 255, 255), CYAN
            core = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            ImageDraw.Draw(core).text((30, th // 2), line, font=font, anchor="lm", fill=col + (255,),
                                      stroke_width=3, stroke_fill=glow_col + (255,))
            glow = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            ImageDraw.Draw(glow).text((30, th // 2), line, font=font, anchor="lm", fill=glow_col + (255,),
                                      stroke_width=10, stroke_fill=glow_col + (255,))
            glow = glow.filter(ImageFilter.GaussianBlur(18))
            items.append((core, glow, li))
        cache.append(items)
    return cache


def tint(img, color):
    r, g, b, a = img.split()
    solid = Image.new("RGBA", img.size, color + (0,))
    solid.putalpha(a)
    return solid


def draw_text(frame, cache, t, dur):
    p = t / dur
    for bi, (s, e, _) in enumerate(BEATS):
        if not (s <= p < e):
            continue
        local = (p - s) * dur
        life = (e - s) * dur
        fade = clamp((life - local) / 0.25)
        for core, glow, li in cache[bi]:
            lt = local - li * 0.16
            if lt < 0:
                continue
            sc = lerp(0.35, 1.0, ease_out_back(lt / 0.38))
            sw, sh = max(8, int(core.width * sc)), max(8, int(core.height * sc))
            c = core.resize((sw, sh), Image.BILINEAR)
            g = glow.resize((sw, sh), Image.BILINEAR)
            cx = W // 2
            if bi == 4:
                cy = 880 + li * 190 + int(14 * math.sin(t * 6 + li))
            else:
                cy = 760 + li * 230
            if bi == 4 and li == 0:
                pulse = 1 + 0.06 * math.sin(t * 9)
                c = c.resize((int(c.width * pulse), int(c.height * pulse)), Image.BILINEAR)
                g = g.resize(c.size, Image.BILINEAR)
            pos = (cx - c.width // 2, cy - c.height // 2)
            if fade < 1:
                for im in (c, g):
                    a = im.getchannel("A").point(lambda v, f=fade: int(v * f))
                    im.putalpha(a)
            layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            layer.alpha_composite(g, (pos[0], pos[1]))
            if lt < 0.30:  # RGB-ajralish (glitch) kirishda
                off = int(26 * (1 - lt / 0.30))
                layer.alpha_composite(tint(c, (255, 0, 80)), (pos[0] - off, pos[1]))
                layer.alpha_composite(tint(c, (0, 220, 255)), (pos[0] + off, pos[1]))
            layer.alpha_composite(c, (pos[0], pos[1]))
            frame.paste(layer, (0, 0), layer)
    return frame


# ---------------------------------------------------------------- 3D ko'cha
def proj(x, y_world, z, cx, hy, cam_h):
    k = F / z
    return cx + x * k, hy + (cam_h - y_world) * k


def tower_params(k):
    r = random.Random(k * 7919 + 13)
    return {
        "h": r.uniform(45, 170),
        "w": r.uniform(10, 18),
        "len": SLOT * r.uniform(0.62, 0.9),
        "base": r.choice([(14, 6, 38), (10, 5, 30), (20, 8, 50), (12, 10, 44)]),
        "neon": r.choice(PAL),
        "sign": r.random() < 0.55,
        "sign_h": r.uniform(10, 40),
        "sign_len": r.uniform(0.15, 0.5),
        "seed": r.random(),
    }


def draw_street(d, t, dist, cx, hy, cam_h):
    # yo'l
    d.rectangle((0, hy, W, H + 600), fill=(8, 3, 26))
    # yo'l bo'ylab chiziqlar (neon)
    for xw, col in ((-X_IN, CYAN), (X_IN, PINK), (-X_IN / 3, VIOLET), (X_IN / 3, VIOLET)):
        for zz0, zz1 in ((Z_MIN, Z_MAX),):
            x0, y0 = proj(xw, 0, zz0, cx, hy, cam_h)
            x1, y1 = proj(xw, 0, zz1, cx, hy, cam_h)
            d.line((x0, y0, x1, y1), fill=col, width=5 if abs(xw) > 4 else 2)
    # ko'ndalang chiziqlar
    step = 6.0
    k0 = int((dist + Z_MIN) // step)
    for k in range(k0, k0 + int((Z_MAX - Z_MIN) / step) + 2):
        z = k * step - dist
        if z < Z_MIN or z > Z_MAX:
            continue
        fog = clamp(z / Z_MAX) ** 0.5
        col = mix(PINK if k % 2 else CYAN, FOG, fog)
        xa, ya = proj(-X_IN, 0, z, cx, hy, cam_h)
        xb, yb = proj(X_IN, 0, z, cx, hy, cam_h)
        d.line((xa, ya, xb, yb), fill=col, width=max(1, int(3 * (1 - fog) + 1)))
    # markaziy punktir
    k0 = int((dist + Z_MIN) // 5)
    for k in range(k0, k0 + 40):
        z = k * 5.0 - dist
        if Z_MIN < z < 120:
            xa, ya = proj(-0.15, 0, z, cx, hy, cam_h)
            xb, yb = proj(0.15, 0, z + 2.2, cx, hy, cam_h)
            d.rectangle((min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)), fill=mix((255, 255, 255), (120, 40, 140), clamp(z / 120)))

    # minoralar (uzoqdan yaqinga)
    ks = range(int((dist + Z_MIN) // SLOT) - 1, int((dist + Z_MAX) // SLOT) + 2)
    for k in reversed(list(ks)):
        for s in (-1, 1):
            tp = tower_params(k * 2 + (1 if s > 0 else 0))
            z1 = k * SLOT - dist
            z2 = z1 + tp["len"]
            if z2 < Z_MIN * 0.6 or z1 > Z_MAX:
                continue
            z1c = max(z1, 2.0)
            fog = clamp(z1 / Z_MAX) ** 1.4
            base = mix(tp["base"], (90, 25, 120), fog * 0.75)
            side = mix(tuple(int(c * 1.7) + 10 for c in tp["base"]), (110, 30, 130), fog * 0.7)
            xi, xo = X_IN + 1.0, X_IN + 1.0 + tp["w"]
            hh = tp["h"]
            a_b = proj(s * xi, 0, z1c, cx, hy, cam_h)
            a_t = proj(s * xi, hh, z1c, cx, hy, cam_h)
            b_b = proj(s * xi, 0, z2, cx, hy, cam_h)
            b_t = proj(s * xi, hh, z2, cx, hy, cam_h)
            d.polygon([a_b, a_t, b_t, b_b], fill=side)
            # yon devor neon chiziqlari
            for hl, col in ((6, tp["neon"]), (hh * 0.45, PAL[(int(tp["seed"] * 10)) % 4]), (hh * 0.8, tp["neon"])):
                p1 = proj(s * xi, hl, z1c, cx, hy, cam_h)
                p2 = proj(s * xi, hl, z2, cx, hy, cam_h)
                d.line((p1[0], p1[1], p2[0], p2[1]), fill=mix(col, FOG, fog), width=max(1, int(4 * (1 - fog) + 1)))
            # vertikal reklama (neon yozuv taxtasi)
            if tp["sign"]:
                zs1 = z1c + (z2 - z1c) * 0.18
                zs2 = zs1 + (z2 - z1c) * tp["sign_len"]
                blink = 1.0 if (math.sin(t * 7 + tp["seed"] * 40) > -0.6) else 0.25
                sc = mix((0, 0, 0), mix(tp["neon"], FOG, fog * 0.5), blink)
                q = [proj(s * (xi - 0.3), tp["sign_h"] + 22, zs1, cx, hy, cam_h),
                     proj(s * (xi - 0.3), tp["sign_h"], zs1, cx, hy, cam_h),
                     proj(s * (xi - 0.3), tp["sign_h"], zs2, cx, hy, cam_h),
                     proj(s * (xi - 0.3), tp["sign_h"] + 22, zs2, cx, hy, cam_h)]
                d.polygon(q, fill=sc)
            # old devor
            fx0, fy0 = a_b
            fxt, fyt = a_t
            ox, _ = proj(s * xo, 0, z1c, cx, hy, cam_h)
            xl, xr = (min(fx0, ox), max(fx0, ox))
            d.rectangle((xl, fyt, xr, fy0), fill=base)
            # oynalar
            if z1c < 85:
                rows = int(hh // 5.5)
                cols = max(2, int(tp["w"] // 3.2))
                rr = random.Random(int(tp["seed"] * 1e6))
                kk = F / z1c
                for rj in range(1, rows):
                    for ci in range(cols):
                        if rr.random() < 0.38:
                            continue
                        wxw = xi + 0.9 + ci * 3.2
                        wy = rj * 5.5
                        px, py = proj(s * wxw, wy, z1c, cx, hy, cam_h)
                        flick = 0.55 + 0.45 * math.sin(t * rr.uniform(1, 4) + rr.random() * 9)
                        c = mix((0, 0, 0), rr.choice(PAL), clamp(flick))
                        c = mix(c, FOG, fog * 0.7)
                        d.rectangle((px, py, px + 1.9 * kk, py + 2.6 * kk), fill=c)
            # tom antennasi
            ax, ay = proj(s * (xi + tp["w"] / 2), hh, z1c, cx, hy, cam_h)
            d.line((ax, ay, ax, ay - 4.5 * F / z1c * 3), fill=mix(base, (255, 255, 255), 0.4), width=2)
            if int(t * 2 + tp["seed"] * 10) % 2 == 0:
                r = max(2, 0.8 * F / z1c)
                ay2 = ay - 13.5 * F / z1c
                d.ellipse((ax - r, ay2 - r, ax + r, ay2 + r), fill=(255, 40, 40))


def draw_fx(d, t, rain, drones):
    # yomg'ir
    for (x, y0, v, ln, a) in rain:
        y = (y0 + t * v) % (H + 300) - 150
        xx = x - (y * 0.18)
        d.line((xx, y, xx - ln * 0.18, y + ln), fill=(160 + a, 190 + a // 2, 255), width=2)
    # uchuvchi dronlar (neon iz)
    for dr in drones:
        px = (dr["x0"] + t * dr["vx"]) % (W + 600) - 300
        py = dr["y"] + 40 * math.sin(t * dr["f"] + dr["ph"])
        for i in range(10):
            fade = 1 - i / 10
            d.ellipse((px - dr["vx"] * i * 0.012 - 5, py - 5, px - dr["vx"] * i * 0.012 + 5, py + 5),
                      fill=mix((0, 0, 0), dr["c"], fade * 0.9))
        d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=(255, 255, 255))


def render_frame(i, dur, ctx):
    t = i / FPS
    p = t / dur
    sky, sky_hy, skyline, overlay, grains, cache, rain, drones = ctx
    beat = t * 2.0                      # 120 bpm
    pulse = math.exp(-7 * (beat % 1.0))
    # kamera: past burchakdan ko'tariladi, oldinga uchadi
    cam_h = lerp(1.1, 4.2, ease_out_back(clamp(t / 3.2)) if False else clamp(t / 3.5) ** 0.6)
    dist = 26 * t + 3 * t * t * 0.35
    sway = 120 * math.sin(t * 0.8) * clamp(t / 2)
    hy = HORIZON + 80 * math.sin(t * 0.55) - 60 * clamp(t / 3.5) + 18 * pulse
    cx = W / 2 + sway

    frame = Image.new("RGB", (W, H))
    frame.paste(sky, (int(sway * 0.12), int(hy - sky_hy)))
    frame.paste(skyline, (int(-200 + sway * 0.25), int(hy - 620)), skyline)
    d = ImageDraw.Draw(frame)
    draw_street(d, t, dist, cx, hy, cam_h)
    # ufq tumani
    fog_band = Image.new("RGB", (W, 260))
    arr = np.zeros((260, W, 3), np.float32)
    ramp = np.linspace(0, 1, 260)
    ramp = (np.sin(ramp * math.pi) ** 1.5)[:, None]
    for ch in range(3):
        arr[:, :, ch] = ramp * FOG[ch] * 0.22
    fog_band = Image.fromarray(arr.astype(np.uint8))
    frame = ImageChops.add(frame, Image.new("RGB", (W, H)))
    tmp = Image.new("RGB", (W, H))
    tmp.paste(fog_band, (0, int(hy - 150)))
    frame = ImageChops.add(frame, tmp)
    d = ImageDraw.Draw(frame)
    draw_fx(d, t, rain, drones)

    frame = draw_text(frame, cache, t, dur)

    # bloom
    small = frame.resize((W // 4, H // 4), Image.BILINEAR)
    b1 = small.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    b2 = small.filter(ImageFilter.GaussianBlur(12)).resize((W, H), Image.BILINEAR)
    lut1 = [min(255, int(max(0, v - 110) * 1.1)) for v in range(256)]
    lut2 = [min(255, int(max(0, v - 90) * 0.9)) for v in range(256)]
    frame = ImageChops.add(frame, b1.point(lut1 * 3))
    frame = ImageChops.add(frame, b2.point(lut2 * 3))

    # kamera: zum + dutch burchak + silkinish (kick bilan)
    zoom = 1.04 + 0.22 * p + 0.028 * pulse
    ang = math.radians(2.6 * math.sin(t * 0.9) + 1.2 * math.sin(t * 2.3))
    ox = 7 * math.sin(t * 31) * pulse
    oy = 7 * math.cos(t * 27) * pulse
    c, s_ = math.cos(ang) / zoom, math.sin(ang) / zoom
    cxm, cym = W / 2, H / 2
    coef = (c, -s_, cxm - c * cxm + s_ * cym + ox,
            s_, c, cym - s_ * cxm - c * cym + oy)
    frame = frame.transform((W, H), Image.AFFINE, coef, Image.BICUBIC)

    # xromatik aberratsiya (kick bilan kuchayadi)
    sh = int(2 + 7 * pulse)
    r, g, b = frame.split()
    r = ImageChops.offset(r, sh, 0)
    b = ImageChops.offset(b, -sh, 0)
    frame = Image.merge("RGB", (r, g, b))

    # glitch bo'laklari (matn boshlanishida)
    for (s0, e0, _) in BEATS:
        lt = t - s0 * dur
        if 0 <= lt < 0.22:
            rnd = random.Random(i)
            for _ in range(5):
                y0 = rnd.randrange(0, H - 120)
                hh = rnd.randrange(20, 110)
                dx = rnd.randrange(-70, 70)
                strip = frame.crop((0, y0, W, y0 + hh))
                frame.paste(ImageChops.offset(strip, dx, 0), (0, y0))

    # chaqnash (flash) — har 4 zarbada
    fl = math.exp(-9 * ((t * 0.5) % 1.0)) * 0.35 if int(t * 0.5) % 2 == 0 else 0
    if fl > 0.02:
        frame = ImageChops.add(frame, Image.new("RGB", (W, H), (int(80 * fl), int(30 * fl), int(110 * fl))))

    frame = ImageChops.multiply(frame, overlay)
    frame = Image.blend(frame, grains[i % 4], 0.045)
    return frame


# ---------------------------------------------------------------- musiqa
def synth_music(path, dur, sr=44100):
    n = int(dur * sr)
    out = np.zeros(n, np.float32)
    bpm = 120
    beat = 60 / bpm
    chords = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]  # C G Am F

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    def add(sig, start):
        i0 = int(start * sr)
        if i0 >= n:
            return
        seg = sig[: n - i0]
        out[i0: i0 + len(seg)] += seg

    def tone(freq, length, amp, kind="saw"):
        tt = np.arange(int(length * sr)) / sr
        if kind == "saw":
            w = 2 * ((tt * freq) % 1.0) - 1
            w = 0.6 * w + 0.4 * np.sign(np.sin(2 * np.pi * freq * tt))
        else:
            w = np.sin(2 * np.pi * freq * tt)
        env = np.minimum(1, tt / 0.005) * np.exp(-tt * (7 if kind == "saw" else 3.2))
        return (w * env * amp).astype(np.float32)

    steps = int(dur / (beat / 2)) + 1
    for s in range(steps):
        tstart = s * beat / 2
        bar = int(tstart // (beat * 4)) % 4
        ch = chords[bar]
        pat = [0, 1, 2, 1, 0, 2, 1, 2]
        note = ch[pat[s % 8]] + 12 + (12 if (s % 16) >= 8 else 0)
        add(tone(hz(note), 0.30, 0.20), tstart)
        if s % 2 == 0:
            add(tone(hz(ch[0] - 24), 0.45, 0.42, "sine"), tstart)
        # kick
        if s % 2 == 0:
            tt = np.arange(int(0.22 * sr)) / sr
            f = 120 * np.exp(-tt * 22) + 42
            k = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 13) * 0.9
            add(k.astype(np.float32), tstart)
        else:  # hi-hat
            rng = np.random.default_rng(s)
            tt = np.arange(int(0.07 * sr)) / sr
            hh = rng.standard_normal(len(tt)) * np.exp(-tt * 70) * 0.16
            add(hh.astype(np.float32), tstart)
        if s % 4 == 2:  # klap
            rng = np.random.default_rng(100 + s)
            tt = np.arange(int(0.16 * sr)) / sr
            cl = rng.standard_normal(len(tt)) * np.exp(-tt * 28) * 0.28
            add(cl.astype(np.float32), tstart)
    fade = int(sr * 0.8)
    out[-fade:] *= np.linspace(1, 0, fade)
    out /= max(1e-6, np.abs(out).max())
    pcm = (out * 0.8 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- asosiy
def build_ctx():
    sky, sky_hy = make_sky()
    skyline = make_skyline()
    overlay, grains = make_overlays()
    cache = build_text_cache()
    rnd = random.Random(3)
    rain = [(rnd.uniform(-200, W + 100), rnd.uniform(0, H + 300), rnd.uniform(1500, 2400), rnd.uniform(40, 90),
             rnd.randrange(0, 30)) for _ in range(130)]
    drones = [{"x0": rnd.uniform(0, W), "y": rnd.uniform(160, 700), "vx": rnd.choice([-1, 1]) * rnd.uniform(160, 420),
               "f": rnd.uniform(1, 3), "ph": rnd.uniform(0, 6), "c": rnd.choice(PAL)} for _ in range(9)]
    return sky, sky_hy, skyline, overlay, grains, cache, rain, drones


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, default=15.5)
    ap.add_argument("--video")
    ap.add_argument("--music")
    ap.add_argument("--preview", help="vergul bilan soniyalar, PNG sinov")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    if a.music:
        synth_music(a.music, a.dur + 0.5)
        print("musiqa tayyor:", a.music)

    ctx = build_ctx()
    if a.preview:
        for sec in a.preview.split(","):
            i = int(float(sec) * FPS)
            fr = render_frame(i, a.dur, ctx)
            p = Path(a.out) / f"prev_{sec}.png"
            fr.resize((540, 960)).save(p)
            print("kadr:", p)
        return
    if a.video:
        total = int(a.dur * FPS)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.video]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(total):
            pr.stdin.write(render_frame(i, a.dur, ctx).tobytes())
            if i % 60 == 0:
                print(f"kadr {i}/{total}", flush=True)
        pr.stdin.close()
        pr.wait()
        print("video tayyor:", a.video)


if __name__ == "__main__":
    main()
