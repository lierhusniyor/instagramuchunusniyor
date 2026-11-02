"""Bitta ssenariydan 1080x1920 Reels — "180 kun" uslubi (Axror prezentatsiyasidan).

Uslub: qorong'i fon #15141B, olov-to'q sariq #FF6A2B, muz-ko'k #3FC8E8, krem #F3EFE6.
Shriftlar: Oswald (katta sarlavha), Rubik (matn), JetBrains Mono (terminal/tizim oynasi).
Sahnalar: terminal + ilgak -> [TIZIM] vazifa oynasi -> krem karta -> to'q sariq bayonot -> konfetti final.
Qahramon yo'q. Har videoda "KUN N / 180" va progress chizig'i.

python3 make_video.py --id h001 --out out/h001.mp4 [--no-voice]
Ovoz: edge-tts (uz-UZ-SardorNeural). O'rnatilmagan bo'lsa yoki --no-voice, ovozsiz (musiqa bilan).
"""
import argparse
import json
import math
import random
import re
import shutil
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
W, H, FPS = 1080, 1920, 30
FONTS = HERE / "fonts"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
VOICE = "uz-UZ-SardorNeural"
CTA_VOICE = "Sen uddalaysan. Obuna bo'l, 180 kunlik yo'lni birga o'tamiz."
HANDLE = "@usniy_or"
TOTAL_DAYS = 180
GAP = 0.35

BG = (21, 20, 27)
PANEL = (34, 31, 44)
FIRE = (255, 106, 43)
ICE = (63, 200, 232)
CREAM = (243, 239, 230)
MUTED = (185, 180, 198)
INK = (21, 20, 27)
OK = (86, 211, 100)

EMOJIS = {"#ozgarish": "🔥", "#organish": "📚", "#it": "💻", "#suniyintellekt": "🧠",
          "#intizom": "⏰", "#pul": "💰", "#sogliq": "💪", "#ingliztili": "🗣️", "#blogger": "🎬"}


# ---------- ovoz ----------
def tts(text, path):
    if not shutil.which("edge-tts"):
        return False
    r = subprocess.run(["edge-tts", "--voice", VOICE, "--rate=+8%", "--text", text,
                        "--write-media", str(path)], capture_output=True)
    return r.returncode == 0 and path.exists() and path.stat().st_size > 1000


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def estimate(text):
    return 0.9 + 0.42 * len(text.split())


# ---------- musiqa (o'zimizniki, mualliflik muammosi yo'q) ----------
def music(path, seconds, sr=44100):
    """Ritmik, ko'taruvchi fon: minor akkordlar, kick, hi-hat, bas."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    bpm = 110
    beat = 60 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    out = np.zeros(n)
    bar = beat * 4
    for i in range(int(seconds / bar) + 1):
        s, e = int(i * bar * sr), min(n, int((i + 1) * bar * sr))
        if s >= n:
            break
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt / 0.15) * np.exp(-tt / 2.5)
        for m in chords[i % 4]:
            f = 440 * 2 ** ((m - 69) / 12)
            out[s:e] += 0.07 * env * (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt))
        bass = 440 * 2 ** ((chords[i % 4][0] - 24 - 69) / 12)
        out[s:e] += 0.16 * np.minimum(1, tt / 0.02) * np.sin(2 * np.pi * bass * tt)
    rng = np.random.default_rng(1)
    for k in range(int(seconds / beat) + 1):
        s = int(k * beat * sr)
        if s >= n:
            break
        L = min(int(0.25 * sr), n - s)
        tt = np.arange(L) / sr
        kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 35)) * tt) * np.exp(-tt * 11)
        out[s:s + L] += 0.42 * kick
        for half in (0.5,):
            h = s + int(beat * half * sr)
            if h < n:
                L = min(int(0.05 * sr), n - h)
                out[h:h + L] += 0.06 * rng.standard_normal(L) * np.exp(-np.arange(L) / sr * 90)
    fade = int(1.0 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------- shriftlar ----------
@lru_cache(maxsize=None)
def font(name, size, weight=700):
    f = ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def OSW(size, w=700):
    return font("Oswald", size, w)


def RUB(size, w=500):
    return font("Rubik", size, w)


def MONO(size, w=700):
    return font("JetBrainsMono", size, w)


@lru_cache(maxsize=None)
def emoji(ch, size):
    try:
        ef = ImageFont.truetype(EMOJI_FONT, 109)
    except Exception:
        return None
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=ef, embedded_color=True)
    bb = im.getbbox()
    if not bb:
        return None
    im = im.crop(bb)
    k = size / max(im.size)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def wrap(text, f, maxw):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(text, maker, sizes, maxw, maxlines):
    for s in sizes:
        f = maker(s)
        lines = wrap(text, f, maxw)
        if len(lines) <= maxlines:
            return f, lines
    return f, lines


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t):
    t = max(0.0, min(1.0, t))
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def fade(img, a):
    if a >= 0.999:
        return img
    im = img.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, a))))
    return im


# ---------- fon ----------
def background(hue_shift=0):
    """Qorong'i fon + sekin suzuvchi nur dog'lari uchun katta kanva."""
    base = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((380, -320, 1400, 700), fill=(44, 35, 71, 255))          # binafsha, yuqori o'ng
    d.ellipse((-420, 1250, 620, 2250), fill=(58, 28, 16, 255))         # cho'g', past chap
    d.ellipse((700, 1500, 1300, 2100), fill=(18, 48, 74, 200))         # muz, past o'ng
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    base.alpha_composite(glow)
    # nozik to'r (kod/terminal hissi)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 90):
        g.line((x, 0, x, H), fill=(255, 255, 255, 7))
    for y in range(0, H, 90):
        g.line((0, y, W, y), fill=(255, 255, 255, 7))
    base.alpha_composite(grid)
    return base


def sparks(n=26, seed=5):
    rnd = random.Random(seed)
    return [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 5), rnd.uniform(30, 90),
             rnd.choice([FIRE, FIRE, ICE])) for _ in range(n)]


def draw_sparks(frame, items, tsec):
    d = ImageDraw.Draw(frame)
    for x, y, r, sp, col in items:
        yy = (y - sp * tsec) % H
        xx = x + 12 * math.sin(tsec * 1.3 + y)
        a = int(110 + 80 * math.sin(tsec * 3 + x))
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=col + (a,))


# ---------- doimiy yuqori panel ----------
def top_layer(day):
    lay = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text((64, 70), f"KUN {day}", font=OSW(64, 700), fill=CREAM)
    x = 64 + d.textlength(f"KUN {day}", font=OSW(64, 700)) + 16
    d.text((x, 90), f"/ {TOTAL_DAYS}", font=OSW(40, 500), fill=MUTED)
    tag = "O'RGAN · O'ZGAR"
    tw = d.textlength(tag, font=MONO(26))
    d.text((W - 64 - tw, 96), tag, font=MONO(26), fill=FIRE)
    # progress
    y0 = 170
    d.rounded_rectangle((64, y0, W - 64, y0 + 14), radius=7, fill=(39, 35, 48, 255))
    frac = max(0.02, min(1, day / TOTAL_DAYS))
    pw = int((W - 128) * frac)
    grad = np.linspace(0, 1, max(2, pw))[None, :, None]
    arr = (np.array(FIRE) * (1 - grad) + np.array(ICE) * grad).astype(np.uint8)
    bar = Image.fromarray(np.repeat(arr, 14, axis=0), "RGB").convert("RGBA")
    mask = Image.new("L", bar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bar.width - 1, 13), radius=7, fill=255)
    lay.paste(bar, (64, y0), mask)
    return lay


def bottom_layer():
    lay = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tw = d.textlength(HANDLE, font=RUB(34, 500))
    d.text(((W - tw) / 2, 40), HANDLE, font=RUB(34, 500), fill=MUTED)
    return lay


# ---------- sahnalar ----------
class Scene:
    """draw(frame, local_t, dur) — sahnani kadrga chizadi."""


class HookScene(Scene):
    def __init__(self, text, day):
        self.cmd = f"$ ./hayot --kun {day} --level-up"
        words = text.upper().split()
        f, lines = fit(text.upper(), lambda s: OSW(s, 700), [150, 132, 116, 102, 90], W - 140, 5)
        self.f, self.lines = f, lines
        self.hl = words[-1] if words else ""
        self.term = self._terminal()

    def _terminal(self):
        tw, th = W - 128, 150
        im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, tw - 1, th - 1), radius=24, fill=(13, 12, 18, 255), outline=ICE, width=3)
        for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
            d.ellipse((28 + i * 34, 22, 48 + i * 34, 42), fill=c)
        return im

    def draw(self, frame, t, dur):
        # terminal yozilishi
        term = self.term.copy()
        d = ImageDraw.Draw(term)
        n = int(len(self.cmd) * min(1, t / 0.7))
        d.text((32, 70), self.cmd[:n], font=MONO(38), fill=ICE)
        if int(t * 3) % 2 == 0 or n < len(self.cmd):
            cx = 32 + d.textlength(self.cmd[:n], font=MONO(38)) + 6
            d.rectangle((cx, 74, cx + 20, 112), fill=FIRE)
        frame.alpha_composite(term, (64, 300))
        # katta ilgak: so'zma-so'z "zarb" bilan
        lh = int(self.f.size * 1.08)
        y = 520 + max(0, (900 - lh * len(self.lines)) // 2) - 80
        widx = 0
        dd = ImageDraw.Draw(frame)
        for ln in self.lines:
            x = 70
            for w in ln.split():
                appear = 0.35 + widx * 0.11
                k = (t - appear) / 0.22
                if k > 0:
                    a = ease_out(k)
                    col = ICE if (w == self.hl and widx == sum(len(l.split()) for l in self.lines) - 1) else CREAM
                    lay = Image.new("RGBA", (int(dd.textlength(w, font=self.f)) + 20, lh + 30), (0, 0, 0, 0))
                    ImageDraw.Draw(lay).text((0, 0), w, font=self.f, fill=col)
                    off = int(40 * (1 - a))
                    frame.alpha_composite(fade(lay, a), (int(x), y + off))
                x += dd.textlength(w + " ", font=self.f)
                widx += 1
            y += lh
        # pastki chiziq
        k = ease_out((t - 0.5) / 0.6)
        dd.rectangle((70, y + 30, 70 + int(380 * k), y + 42), fill=FIRE)


class SystemScene(Scene):
    """Manhva uslubidagi [TIZIM] oynasi."""

    def __init__(self, text, idx, total):
        self.idx, self.total = idx, total
        self.f, self.lines = fit(text, lambda s: OSW(s, 600), [92, 82, 74, 66], W - 260, 6)
        lh = int(self.f.size * 1.18)
        self.box_h = 210 + lh * len(self.lines) + 150
        self.lh = lh

    def draw(self, frame, t, dur):
        a = ease_out(t / 0.35)
        bw, bh = W - 128, self.box_h
        x0, y0 = 64, (H - bh) // 2 + 40
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((x0 - 10, y0 - 10, x0 + bw + 10, y0 + bh + 10), radius=26,
                                                fill=ICE + (int(90 * a * (0.85 + 0.15 * math.sin(t * 5))),))
        frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(28)))
        box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        d = ImageDraw.Draw(box)
        d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=18, fill=(14, 26, 38, 245), outline=ICE, width=4)
        head = f"[ TIZIM ] · VAZIFA {self.idx}/{self.total}"
        n = int(len(head) * min(1, t / 0.5))
        d.text((48, 50), head[:n], font=MONO(34), fill=ICE)
        d.line((48, 120, bw - 48, 120), fill=(63, 200, 232, 120), width=2)
        y = 165
        for i, ln in enumerate(self.lines):
            k = ease_out((t - 0.25 - 0.12 * i) / 0.3)
            if k > 0:
                lay = Image.new("RGBA", (bw, self.lh + 20), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((0, 0), ln, font=self.f, fill=(230, 247, 252))
                box.alpha_composite(fade(lay, k), (48 + int(30 * (1 - k)), y))
            y += self.lh
        k = ease_out((t - 0.8) / 0.3)
        if k > 0:
            d.text((48, bh - 90), "QABUL QILINDI  ✓" if False else "QABUL QILINDI", font=MONO(32), fill=FIRE + (int(255 * k),))
            d.text((bw - 48 - d.textlength("XP +10", font=MONO(32)), bh - 90), "XP +10",
                   font=MONO(32), fill=OK + (int(255 * k),))
        sc = 0.9 + 0.1 * ease_back(t / 0.4)
        if sc < 0.999:
            box = box.resize((int(bw * sc), int(bh * sc)), Image.BILINEAR)
        frame.alpha_composite(fade(box, a), (x0 + (bw - box.width) // 2, y0 + (bh - box.height) // 2))


class CardScene(Scene):
    """Krem karta, raqam va emoji (prezentatsiyadagi "mem" kartalari kabi)."""

    def __init__(self, text, idx, emo):
        self.idx, self.emo = idx, emo
        self.f, self.lines = fit(text, lambda s: RUB(s, 700), [76, 68, 60, 54], W - 260, 7)
        self.lh = int(self.f.size * 1.25)

    def draw(self, frame, t, dur):
        k = ease_out(t / 0.4)
        cw = W - 128
        ch = 300 + self.lh * len(self.lines) + 80
        card = Image.new("RGBA", (cw + 16, ch + 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(card)
        d.rectangle((16, 16, cw + 15, ch + 15), fill=(0, 0, 0, 255))           # qattiq soya
        d.rectangle((0, 0, cw - 1, ch - 1), fill=CREAM, outline=INK, width=5)
        num = f"{self.idx:02d}"
        d.text((56, 40), num, font=OSW(150, 700), fill=FIRE)
        em = emoji(self.emo, 150)
        if em:
            bob = int(10 * math.sin(t * 4))
            card.alpha_composite(em, (cw - 56 - em.width, 50 + bob))
        y = 260
        for i, ln in enumerate(self.lines):
            kk = ease_out((t - 0.2 - 0.1 * i) / 0.3)
            if kk > 0:
                lay = Image.new("RGBA", (cw, self.lh + 20), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((0, 0), ln, font=self.f, fill=INK)
                card.alpha_composite(fade(lay, kk), (56, y))
            y += self.lh
        x = int(64 + (W) * (1 - k))  # o'ngdan "push"
        rot = card.rotate(-2 * (1 - k), resample=Image.BICUBIC, expand=False)
        frame.alpha_composite(rot, (x, (H - ch) // 2 + 30))


class FireScene(Scene):
    """To'liq to'q sariq bayonot sahnasi."""

    def __init__(self, text, idx):
        self.idx = idx
        self.f, self.lines = fit(text.upper(), lambda s: OSW(s, 700), [128, 112, 100, 88, 78], W - 150, 6)
        self.lh = int(self.f.size * 1.1)

    def draw(self, frame, t, dur):
        k = ease_out(t / 0.35)
        # pastdan ko'tariluvchi to'q sariq panel
        top = int(H - (H - 250) * k)
        d = ImageDraw.Draw(frame)
        d.rectangle((0, top, W, H), fill=FIRE)
        if k < 0.6:
            return
        d.text((72, 360), "ESDA TUT", font=MONO(36), fill=INK)
        total_h = self.lh * len(self.lines)
        y = (H - total_h) // 2 + 40
        for i, ln in enumerate(self.lines):
            kk = ease_back((t - 0.3 - 0.1 * i) / 0.35)
            if kk > 0:
                lay = Image.new("RGBA", (W, self.lh + 30), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((0, 0), ln, font=self.f, fill=INK)
                sc = max(0.01, kk)
                if abs(sc - 1) > 0.01:
                    lay = lay.resize((max(1, int(W * sc)), max(1, int((self.lh + 30) * sc))), Image.BILINEAR)
                frame.alpha_composite(lay, (72, y + int((self.lh) * (1 - sc) / 2)))
            y += self.lh
        kk = ease_out((t - 0.9) / 0.4)
        d.rectangle((72, y + 40, 72 + int(260 * kk), y + 56), fill=INK)


class FinalScene(Scene):
    def __init__(self, day):
        self.day = day
        rnd = random.Random(day)
        cols = [FIRE, ICE, CREAM, OK]
        self.conf = [(rnd.uniform(0, W), rnd.uniform(-H, 0), rnd.uniform(380, 700), rnd.uniform(0, 6.28),
                      rnd.uniform(2, 6), cols[i % 4]) for i in range(70)]

    def draw(self, frame, t, dur):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((90, 520, 990, 1420), fill=(58, 28, 16, int(255 * ease_out(t / 0.5))))
        frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
        d = ImageDraw.Draw(frame)
        for x, y, sp, ph, rs, col in self.conf:
            yy = y + sp * t
            if -40 < yy < H + 40:
                ang = ph + rs * t
                w2, h2 = 9 * abs(math.cos(ang)) + 2, 15
                d.rectangle((x - w2, yy - h2, x + w2, yy + h2), fill=col + (200,))
        k = ease_back(t / 0.45)
        t1 = "SEN"
        t2 = "UDDALAYSAN"
        for txt, size, y, col, delay in [(t1, 170, 640, CREAM, 0), (t2, 170, 820, FIRE, 0.12)]:
            kk = ease_back((t - delay) / 0.45)
            if kk <= 0:
                continue
            f = OSW(size, 700)
            tw = d.textlength(txt, font=f)
            lay = Image.new("RGBA", (int(tw) + 20, size + 60), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((0, 0), txt, font=f, fill=col)
            sc = max(0.05, kk)
            lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
            frame.alpha_composite(lay, (int((W - lay.width) / 2), y + int(80 * (1 - sc))))
        kk = ease_out((t - 0.5) / 0.4)
        if kk > 0:
            s = f"Kun {self.day} bajarildi. Ertaga — kun {self.day + 1}."
            f = RUB(44, 500)
            tw = d.textlength(s, font=f)
            d.text(((W - tw) / 2, 1060), s, font=f, fill=CREAM + (int(255 * kk),))
            s2 = "Obuna bo'l — 180 kunni birga o'tamiz"
            f2 = RUB(40, 700)
            tw = d.textlength(s2, font=f2)
            bx = (W - tw) / 2
            d.rounded_rectangle((bx - 36, 1160, bx + tw + 36, 1250), radius=45, fill=FIRE + (int(255 * kk),))
            d.text((bx, 1180), s2, font=f2, fill=INK + (int(255 * kk),))


# ---------- yig'ish ----------
def day_of(script):
    m = re.match(r"h(\d+)", script.get("id", ""))
    return int(m.group(1)) if m else 1


def build_scenes(script, day):
    tag = (script.get("tags") or ["#ozgarish"])[0]
    emo = EMOJIS.get(tag, "🔥")
    kinds = [["sys", "card", "fire"], ["card", "sys", "fire"], ["sys", "fire", "card"]][day % 3]
    n = len(script["lines"])
    scenes = [HookScene(script["hook"], day)]
    for i, (kind, text) in enumerate(zip(kinds * 3, script["lines"]), 1):
        if kind == "sys":
            scenes.append(SystemScene(text, i, n))
        elif kind == "card":
            scenes.append(CardScene(text, i, emo))
        else:
            scenes.append(FireScene(text, i))
    scenes.append(FinalScene(day))
    return scenes


def render(script, out, voice=True, day=None):
    day = day or day_of(script)
    texts = [script["hook"]] + list(script["lines"]) + [CTA_VOICE]
    tmp = Path(tempfile.mkdtemp())
    audio, durs = [], []
    for i, text in enumerate(texts):
        p = tmp / f"v{i}.mp3"
        if voice and tts(text, p):
            audio.append(p)
            durs.append(max(duration(p), 1.6))
        else:
            audio.append(None)
            durs.append(max(estimate(text), 1.8))
    starts, t = [], 0.3
    for dd in durs:
        starts.append(t)
        t += dd + GAP
    total = t + 0.5
    ends = starts[1:] + [total]

    bg = background()
    top = top_layer(day)
    bottom = bottom_layer()
    sp = sparks(seed=day)
    scenes = build_scenes(script, day)

    nframes = int(total * FPS)
    silent = tmp / "silent.mp4"
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for fi in range(nframes):
        tsec = fi / FPS
        seg = max([i for i, s in enumerate(starts) if s <= tsec] or [0])
        local = tsec - starts[seg]
        frame = bg.copy()
        draw_sparks(frame, sp, tsec)
        scenes[seg].draw(frame, local, ends[seg] - starts[seg])
        # chiqish: oxirgi 0.18 s da qorayib o'tish
        left = ends[seg] - tsec
        if seg < len(scenes) - 1 and left < 0.18:
            ov = Image.new("RGBA", (W, H), BG + (int(255 * (1 - left / 0.18)),))
            frame.alpha_composite(ov)
        frame.alpha_composite(top, (0, 0))
        frame.alpha_composite(bottom, (0, H - 150))
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg video xatosi")

    mus = tmp / "music.wav"
    music(mus, total)
    inputs, filters, labels = ["-i", str(silent), "-i", str(mus)], ["[1:a]volume=0.32[m]"], ["[m]"]
    for i, p in enumerate(audio):
        if p:
            inputs += ["-i", str(p)]
            idx = len(inputs) // 2 - 1
            ms = int(starts[i] * 1000)
            filters.append(f"[{idx}:a]adelay={ms}|{ms},volume=1.6[a{i}]")
            labels.append(f"[a{i}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,alimiter=limit=0.95[out]")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_suffix(".part.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
                        "-map", "0:v", "-map", "[out]", "-t", f"{total:.2f}", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(part)])
    if r.returncode != 0:
        raise SystemExit("ffmpeg audio xatosi")
    part.rename(out)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"seconds": round(total, 1), "voice": all(audio), "day": day}


def load(script_id):
    for s in json.loads((HERE / "scripts.json").read_text(encoding="utf-8")):
        if s["id"] == script_id:
            return s
    raise SystemExit(f"Ssenariy topilmadi: {script_id}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-voice", action="store_true")
    a = ap.parse_args()
    print(render(load(a.id), a.out, voice=not a.no_voice))
