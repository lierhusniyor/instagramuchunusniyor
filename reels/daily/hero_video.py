"""Qahramonli "level-up" Reels — USTOZ (muallif) gapiradi, tizim oynalari, boss, kvest, XP.

180 kun uslubi (ranglar/shriftlar make_video.py dan). Qahramon USTOZ — o'zimizning original personaj:
kapyushonli siluet, muz rang ko'zlar, ovoz balandligiga qarab og'iz harakati, ko'z qisish, nafas.
Matn so'zma-so'z chiqadi (karaoke), joriy so'z olov rangda.

python3 hero_video.py --id h002 --out out/h002.mp4 [--no-voice]
Ovoz: edge-tts (uz-UZ-SardorNeural) + so'z vaqtlari (WordBoundary). Bo'lmasa, vaqt taxmin qilinadi.
"""
import argparse
import asyncio
import json
import math
import random
import shutil
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_video as mv
from make_video import (BG, CREAM, FIRE, FPS, H, ICE, INK, MONO, MUTED, OK, OSW, PANEL, RUB, W,
                        ease_back, ease_out, emoji, wrap)

HERE = Path(__file__).parent
SR = 44100
VOICE = "uz-UZ-SardorNeural"
STAGE_Y = 250          # oynalar markazi shu oraliqda
CAP_Y = 1150           # subtitr
HERO_Y = 1310          # qahramon tepasi


# ================= ovoz =================
async def _tts_words(text, mp3):
    import edge_tts
    try:
        comm = edge_tts.Communicate(text, VOICE, rate="+12%", boundary="WordBoundary")
    except TypeError:
        comm = edge_tts.Communicate(text, VOICE, rate="+12%")
    words = []
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    return words


def tts(text, mp3):
    try:
        words = asyncio.run(_tts_words(text, mp3))
    except Exception as e:
        print("TTS yo'q:", e)
        return None
    if not mp3.exists() or mp3.stat().st_size < 1000:
        return None
    return words


def to_wav_array(mp3):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1",
                        "-ar", str(SR), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def guess_words(text, start=0.15):
    out, t = [], start
    for w in text.split():
        d = 0.16 + 0.065 * len(w.strip(",.?!—"))
        out.append((t, t + d, w))
        t += d + (0.22 if w[-1] in ",.?!" else 0.04)
    return out


# ================= ovoz effektlari va musiqa =================
def sfx(kind):
    rng = np.random.default_rng(7)
    if kind == "whoosh":
        n = int(0.45 * SR); t = np.arange(n) / SR
        noise = rng.standard_normal(n)
        k = np.exp(-((t - 0.22) / 0.12) ** 2)
        lo = np.convolve(noise, np.ones(30) / 30, "same")
        return 0.35 * lo * k
    if kind == "ding":
        n = int(0.7 * SR); t = np.arange(n) / SR
        return 0.25 * (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6)
    if kind == "impact":
        n = int(0.6 * SR); t = np.arange(n) / SR
        boom = np.sin(2 * np.pi * (40 + 120 * np.exp(-t * 20)) * t) * np.exp(-t * 6)
        crack = rng.standard_normal(n) * np.exp(-t * 40)
        return 0.7 * boom + 0.25 * crack
    if kind == "levelup":
        out = np.zeros(int(1.2 * SR))
        for i, m in enumerate([72, 76, 79, 84]):
            s = int(i * 0.09 * SR); t = np.arange(int(0.6 * SR)) / SR
            f = 440 * 2 ** ((m - 69) / 12)
            tone = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 5)
            out[s:s + len(t)] += 0.18 * tone[: len(out) - s]
        return out
    if kind == "glitch":
        n = int(0.35 * SR)
        sq = np.sign(np.sin(2 * np.pi * 180 * np.arange(n) / SR))
        gate = (rng.random(n // 400 + 1) > 0.4).repeat(400)[:n]
        return 0.15 * sq * gate + 0.1 * rng.standard_normal(n) * gate
    return np.zeros(1)


def put(buf, x, at):
    s = int(at * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


# ================= qahramon USTOZ =================
HW, HH = 560, 600  # sprite o'lchami


@lru_cache(maxsize=None)
def hero_sprite(blink, mouth):
    """blink 0..3 (3 = yopiq), mouth 0..4. 2x chizib kichraytiriladi (silliq qirralar)."""
    S = 2
    im = Image.new("RGBA", (HW * S, HH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = HW * S // 2
    # yelka/tana
    d.rounded_rectangle((cx - 250 * S, 430 * S, cx + 250 * S, 700 * S), radius=120 * S, fill=(30, 27, 40, 255))
    # kapyushon
    d.ellipse((cx - 190 * S, 40 * S, cx + 190 * S, 470 * S), fill=(36, 32, 48, 255))
    d.polygon([(cx - 190 * S, 300 * S), (cx - 230 * S, 520 * S), (cx + 230 * S, 520 * S), (cx + 190 * S, 300 * S)],
              fill=(36, 32, 48, 255))
    # yuz (soya)
    d.ellipse((cx - 125 * S, 150 * S, cx + 125 * S, 440 * S), fill=(13, 12, 18, 255))
    # ko'krak belgisi
    d.rounded_rectangle((cx - 70 * S, 520 * S, cx + 70 * S, 575 * S), radius=14 * S, outline=FIRE + (255,), width=4 * S)
    d.text((cx, 548 * S), "180", font=OSW(38 * S, 700), fill=FIRE, anchor="mm")
    # ko'zlar (porlash qatlami alohida)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    eh = [26, 18, 8, 2][blink] * S
    for sx in (-1, 1):
        ex = cx + sx * 58 * S
        ey = 280 * S
        box = (ex - 38 * S, ey - eh // 2, ex + 38 * S, ey + eh // 2)
        g.ellipse(box, fill=ICE + (255,))
    # og'iz
    mh = [3, 10, 18, 26, 34][mouth] * S
    mbox = (cx - (34 + mouth * 4) * S, 370 * S - mh // 2, cx + (34 + mouth * 4) * S, 370 * S + mh // 2)
    g.rounded_rectangle(mbox, radius=max(2, mh // 2), fill=ICE + (230,))
    blur = glow.filter(ImageFilter.GaussianBlur(14 * S))
    im.alpha_composite(blur)
    im.alpha_composite(blur)
    im.alpha_composite(glow)
    # kapyushon chetidagi olov nur (rim light)
    rim = Image.new("RGBA", im.size, (0, 0, 0, 0))
    r = ImageDraw.Draw(rim)
    r.arc((cx - 190 * S, 40 * S, cx + 190 * S, 470 * S), 190, 350, fill=FIRE + (255,), width=7 * S)
    rim = rim.filter(ImageFilter.GaussianBlur(3 * S))
    im.alpha_composite(rim)
    return im.resize((HW, HH), Image.LANCZOS)


@lru_cache(maxsize=None)
def hero_aura():
    a = Image.new("RGBA", (HW + 300, HH + 300), (0, 0, 0, 0))
    ImageDraw.Draw(a).ellipse((150, 120, HW + 150, HH + 150), fill=(63, 200, 232, 70))
    return a.filter(ImageFilter.GaussianBlur(70))


@lru_cache(maxsize=None)
def name_tag():
    t = Image.new("RGBA", (300, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle((0, 0, 299, 63), radius=14, fill=(21, 20, 27, 230), outline=ICE + (255,), width=3)
    d.text((150, 32), "USTOZ · LVL ∞", font=MONO(26), fill=ICE, anchor="mm")
    d.text((150, 82), mv.HANDLE, font=RUB(26, 500), fill=MUTED, anchor="mm")
    return t


# ================= UI qismlari =================
def glow_panel(w, h, border, title=None, fill=(28, 26, 38, 240)):
    pad = 60
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + h), radius=26, outline=border + (255,), width=10)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=26, fill=fill, outline=border + (255,), width=4)
    if title:
        d.rounded_rectangle((pad, pad, pad + w, pad + 74), radius=26, fill=border + (40,))
        d.line((pad + 20, pad + 74, pad + w - 20, pad + 74), fill=border + (160,), width=2)
        d.text((pad + w / 2, pad + 38), title, font=MONO(32), fill=border, anchor="mm")
    return im, pad


def center_text(d, y, text, f, fill, cx=None):
    d.text((cx if cx is not None else W / 2, y), text, font=f, fill=fill, anchor="mm")


def bar(d, x, y, w, h, frac, col, back=(45, 40, 58)):
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=back + (255,))
    if frac > 0.01:
        d.rounded_rectangle((x, y, x + max(h, int(w * frac)), y + h), radius=h // 2, fill=col + (255,))


def paste_scaled(frame, card, cx, cy, s, alpha=1.0):
    if s <= 0.02 or alpha <= 0.02:
        return
    im = card if abs(s - 1) < 0.01 else card.resize((max(1, int(card.width * s)), max(1, int(card.height * s))),
                                                    Image.BILINEAR)
    if alpha < 0.99:
        im = mv.fade(im, alpha)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def pop(t, d=0.35):
    return ease_back(t / d) if t < d else 1.0


# ================= sahnalar (beat) =================
class Beat:
    sound = "whoosh"
    shakes = ()

    def __init__(self, spec):
        self.s = spec

    def draw(self, frame, t, dur, words):
        pass


class Alert(Beat):
    sound = "glitch"
    shakes = (0.0,)

    def __init__(self, spec):
        super().__init__(spec)
        card, p = glow_panel(860, 470, FIRE, "⚠  OGOHLANTIRISH  ⚠", fill=(40, 18, 14, 245))
        d = ImageDraw.Draw(card)
        center_text(d, p + 200, spec["big1"], OSW(130), CREAM, card.width / 2)
        center_text(d, p + 340, spec["big2"], OSW(110), FIRE, card.width / 2)
        center_text(d, p + 435, spec.get("small", ""), MONO(28, 500), MUTED, card.width / 2)
        self.card = card

    def draw(self, frame, t, dur, words):
        s = pop(t, 0.3)
        paste_scaled(frame, self.card, W / 2, 700, s)
        # qizil chaqnash (chiroq)
        if int(t * 4) % 2 == 0 and t < 1.6:
            ov = Image.new("RGBA", (W, H), (255, 60, 20, 26))
            frame.alpha_composite(ov)


class Boss(Beat):
    sound = "impact"
    shakes = (0.05,)

    def __init__(self, spec, hp_from=1.0, hp_to=1.0, damage=False):
        super().__init__(spec)
        self.hp_from, self.hp_to, self.damage = hp_from, hp_to, damage
        card, p = glow_panel(860, 560, FIRE, "BOSS JANGI")
        d = ImageDraw.Draw(card)
        cw = card.width
        center_text(d, p + 140, "DUSHMAN", MONO(30, 500), MUTED, cw / 2)
        center_text(d, p + 245, spec["boss"], OSW(150), FIRE, cw / 2)
        center_text(d, p + 360, "LVL 99  ·  HP", MONO(30, 500), CREAM, cw / 2)
        self.card, self.p = card, p
        if damage:
            self.shakes = tuple(spec.get("hits", (0.8, 1.6, 2.4)))
            self.sound = "whoosh"

    def draw(self, frame, t, dur, words):
        cx, cy = W / 2, 700
        s = pop(t, 0.3) if not self.damage else 1.0
        breathe = 1 + 0.012 * math.sin(t * 5)
        paste_scaled(frame, self.card, cx, cy, s * breathe)
        if s < 0.9:
            return
        hits = self.shakes if self.damage else ()
        k = sum(1 for h in hits if t >= h)
        frac = self.hp_from - (self.hp_from - self.hp_to) * (k / max(1, len(hits)))
        d = ImageDraw.Draw(frame)
        x0, y0 = int(cx - 380), int(cy + 145)
        bar(d, x0, y0, 760, 46, frac, FIRE if frac > 0.3 else (230, 60, 60))
        d.text((cx, y0 + 23), f"{int(frac * 9999)} / 9999", font=MONO(26), fill=INK if frac > 0.5 else CREAM,
               anchor="mm")
        for h in hits:  # zarba raqamlari uchadi
            dt = t - h
            if 0 <= dt < 0.9:
                y = cy - 120 - dt * 260
                a = int(255 * (1 - dt / 0.9))
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((cx + 200 + 40 * math.sin(h * 9), y), "-3333", font=OSW(96),
                                         fill=ICE + (a,), anchor="mm")
                frame.alpha_composite(lay)
        if self.damage and frac <= 0.01:
            st = t - hits[-1]
            sc = 1.6 - 0.6 * ease_out(st / 0.25)
            stamp = stamp_img()
            paste_scaled(frame, stamp, cx, cy - 20, sc)


@lru_cache(maxsize=None)
def stamp_img():
    im = Image.new("RGBA", (760, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 750, 210), radius=24, outline=OK + (255,), width=12, fill=(10, 30, 14, 220))
    d.text((380, 112), "MAG'LUB ETILDI", font=OSW(110), fill=OK, anchor="mm")
    return im.rotate(-8, expand=True, resample=Image.BICUBIC)


class Card(Beat):
    sound = "whoosh"

    def __init__(self, spec):
        super().__init__(spec)
        w, h = 880, 520
        im = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((24, 24, w + 23, h + 23), radius=30, fill=(0, 0, 0, 255))
        d.rounded_rectangle((0, 0, w, h), radius=30, fill=CREAM + (255,))
        d.text((60, 60), spec.get("tag", "FAKT"), font=MONO(30), fill=FIRE)
        e = emoji(spec.get("emoji", "🧠"), 120)
        if e:
            im.alpha_composite(e, (w - 60 - e.width, 40))
        f = OSW(92)
        y = 200
        for line in wrap(spec["big"], f, w - 120):
            d.text((60, y), line.upper(), font=f, fill=INK)
            y += 104
        d.text((60, y + 20), spec.get("small", ""), font=RUB(40, 500), fill=(90, 84, 100))
        self.card = im

    def draw(self, frame, t, dur, words):
        s = pop(t)
        ang = (1 - min(1, t / 0.35)) * -6
        c = self.card.rotate(ang, expand=True, resample=Image.BICUBIC) if abs(ang) > 0.2 else self.card
        paste_scaled(frame, c, W / 2, 700, s)


@lru_cache(maxsize=None)
def rays():
    im = Image.new("RGBA", (1400, 1400), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(16):
        a = i * math.pi / 8
        d.polygon([(700, 700), (700 + 900 * math.cos(a - 0.08), 700 + 900 * math.sin(a - 0.08)),
                   (700 + 900 * math.cos(a + 0.08), 700 + 900 * math.sin(a + 0.08))], fill=ICE + (40,))
    return im.filter(ImageFilter.GaussianBlur(6))


class Weapon(Beat):
    sound = "ding"

    def __init__(self, spec):
        super().__init__(spec)
        card, p = glow_panel(860, 480, ICE, "[ TIZIM ]  YANGI QUROL OLINDI")
        d = ImageDraw.Draw(card)
        cw = card.width
        center_text(d, p + 200, spec["big1"], OSW(150), ICE, cw / 2)
        center_text(d, p + 330, spec["big2"], OSW(96), CREAM, cw / 2)
        center_text(d, p + 425, spec.get("small", ""), MONO(28, 500), FIRE, cw / 2)
        self.card = card

    def draw(self, frame, t, dur, words):
        r = rays().rotate(t * 25, resample=Image.BILINEAR)
        paste_scaled(frame, r, W / 2, 700, 0.3 + 0.7 * ease_out(t / 0.5), min(1, t / 0.3))
        paste_scaled(frame, self.card, W / 2, 700, pop(t))


class Items(Beat):
    sound = "whoosh"

    def __init__(self, spec):
        super().__init__(spec)
        self.rows = []
        for emo, a, b in spec["items"]:
            im = Image.new("RGBA", (900, 190), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, 899, 189), radius=24, fill=PANEL + (245,), outline=ICE + (200,), width=3)
            e = emoji(emo, 100)
            if e:
                im.alpha_composite(e, (40, (190 - e.height) // 2))
            d.text((180, 30), a.upper(), font=OSW(56), fill=CREAM)
            d.text((180, 104), "→", font=MONO(46), fill=FIRE)
            d.text((240, 108), b, font=RUB(46, 700), fill=FIRE)
            self.rows.append(im)
        self.title = Image.new("RGBA", (900, 90), (0, 0, 0, 0))
        ImageDraw.Draw(self.title).text((450, 45), spec.get("title", "QANDAY ISHLATILADI"), font=MONO(34),
                                         fill=ICE, anchor="mm")

    def draw(self, frame, t, dur, words):
        frame.alpha_composite(self.title, (90, 300))
        # har bir qator o'z kalit so'zi aytilganda chiqadi
        keys = self.s.get("keys", [])
        for i, row in enumerate(self.rows):
            at = 0.1 + i * (dur - 0.5) / len(self.rows)
            if i < len(keys):
                for (ws, we, w) in words:
                    if keys[i].lower() in w.lower():
                        at = ws
                        break
            lt = t - at
            if lt < 0:
                continue
            x = 90 + int((1 - ease_out(lt / 0.3)) * 700)
            frame.alpha_composite(row, (x, 420 + i * 230))


class Quest(Beat):
    sound = "ding"

    def __init__(self, spec):
        super().__init__(spec)
        card, p = glow_panel(860, 560, ICE, "[ TIZIM ]  KUNLIK KVEST")
        d = ImageDraw.Draw(card)
        cw = card.width
        f = OSW(84)
        y = p + 140
        for line in wrap(spec["quest"].upper(), f, 760):
            center_text(d, y, line, f, CREAM, cw / 2)
            y += 96
        center_text(d, p + 380, "MUKOFOT: +50 XP  ·  INTIZOM +1", MONO(28), FIRE, cw / 2)
        self.card, self.p = card, p
        self.lvl = spec.get("lvl_at", 0.55)

    def draw(self, frame, t, dur, words):
        cy = 640
        paste_scaled(frame, self.card, W / 2, cy, pop(t))
        if t < 0.35:
            return
        d = ImageDraw.Draw(frame)
        fr = min(1, (t - 0.4) / (dur * self.lvl))
        bar(d, W / 2 - 380, cy + 190, 760, 40, ease_out(fr), ICE)
        d.text((W / 2, cy + 210), f"XP {int(50 * ease_out(fr))}/50", font=MONO(24), fill=INK if fr > 0.5 else CREAM,
               anchor="mm")
        lt = t - (0.4 + dur * self.lvl)
        if lt >= 0:
            s = 1.5 - 0.5 * ease_out(lt / 0.3)
            lay = level_up_img()
            paste_scaled(frame, lay, W / 2, cy - 390, s, min(1, lt / 0.15))


@lru_cache(maxsize=None)
def level_up_img():
    im = Image.new("RGBA", (960, 230), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text((480, 80), "LEVEL UP!", font=OSW(140), fill=FIRE + (255,), anchor="mm")
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.text((480, 80), "LEVEL UP!", font=OSW(140), fill=FIRE, anchor="mm")
    d.text((480, 190), "RANK  E  →  D", font=MONO(44), fill=CREAM, anchor="mm")
    return im


KINDS = {"alert": Alert, "boss": Boss, "card": Card, "weapon": Weapon, "items": Items, "quest": Quest}


def make_beat(spec):
    k = spec["kind"]
    if k == "hit":
        return Boss(spec, 1.0, 0.0, damage=True)
    return KINDS[k](spec)


# ================= subtitr (karaoke) =================
@lru_cache(maxsize=4096)
def word_img(word, active):
    f = OSW(78)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = int(d.textlength(word, font=f)) + 20
    im = Image.new("RGBA", (tw, 110), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text((10, 8), word, font=f, fill=FIRE if active else CREAM, stroke_width=6, stroke_fill=(0, 0, 0, 255))
    return im


def draw_caption(frame, words, t):
    if not words:
        return
    # 3 so'zlik guruhlar
    groups = [words[i:i + 3] for i in range(0, len(words), 3)]
    cur = None
    for g in groups:
        if g[0][0] - 0.05 <= t:
            cur = g
    if cur is None:
        return
    if t > cur[-1][1] + 0.6 and cur is groups[-1]:
        return
    imgs = [word_img(w.upper(), ws <= t < we + 0.05) for ws, we, w in cur]
    gap = 18
    total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    x = (W - total) / 2
    gt = t - cur[0][0]
    s = pop(gt, 0.18)
    for (ws, we, w), im in zip(cur, imgs):
        sc = s * (1.12 if ws <= t < we else 1.0)
        paste_scaled(frame, im, x + im.width / 2, CAP_Y + 55, sc)
        x += im.width + gap


# ================= asosiy =================
def render(script, out, voice=True):
    day = int(script["id"].lstrip("h").split("-")[0])
    tmp = Path(tempfile.mkdtemp())
    beats = script["beats"]
    voices, words_all, durs = [], [], []
    for i, b in enumerate(beats):
        mp3 = tmp / f"v{i}.mp3"
        words = tts(b["say"], mp3) if voice else None
        if words is not None:
            arr = to_wav_array(mp3)
            voices.append(arr)
            if not words:
                words = guess_words(b["say"])
                scale = (len(arr) / SR) / (words[-1][1] + 0.2)
                words = [(a * scale, c * scale, w) for a, c, w in words]
            durs.append(max(len(arr) / SR + 0.25, 1.8))
        else:
            voices.append(None)
            words = guess_words(b["say"])
            durs.append(max(words[-1][1] + 0.45, 1.8))
        words_all.append(words)
    outro = 1.6
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += d
    total = t + outro
    objs = [make_beat(b) for b in beats]

    # --- og'iz amplitudasi (kadr bo'yicha) ---
    nfr = int(total * FPS) + 1
    amp = np.zeros(nfr)
    for i, v in enumerate(voices):
        if v is not None:
            hop = SR // FPS
            for k in range(len(v) // hop):
                fi = int(starts[i] * FPS) + k
                if fi < nfr:
                    amp[fi] = np.sqrt(np.mean(v[k * hop:(k + 1) * hop] ** 2))
        else:
            for ws, we, w in words_all[i]:
                for fi in range(int((starts[i] + ws) * FPS), int((starts[i] + we) * FPS)):
                    if fi < nfr:
                        amp[fi] = 0.08 * (0.6 + 0.4 * abs(math.sin(fi * 1.7)))
    if amp.max() > 0:
        amp = np.convolve(amp, [0.25, 0.5, 0.25], "same") / (np.percentile(amp[amp > 0], 90) + 1e-6)

    # --- silkinish vaqtlari ---
    shakes = [starts[i] + s for i, o in enumerate(objs) for s in o.shakes]

    bg = mv.background()
    top = mv.top_layer(day)
    bottom = mv.bottom_layer()
    sp = mv.sparks(n=40, seed=day)
    rnd = random.Random(day)
    blinks = sorted(rnd.uniform(0.5, total) for _ in range(int(total / 2.6)))
    conf = [(rnd.uniform(0, W), rnd.uniform(-300, 0), rnd.uniform(-60, 60), rnd.uniform(500, 900),
             rnd.choice([FIRE, ICE, CREAM, OK]), rnd.uniform(0, 6)) for _ in range(90)]

    silent = tmp / "v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "19", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for fi in range(nfr - 1):
        ts = fi / FPS
        seg = max([i for i, s in enumerate(starts) if s <= ts] or [0])
        local = ts - starts[seg]
        frame = bg.copy()
        mv.draw_sparks(frame, sp, ts)
        # qahramon (doim pastda)
        a = amp[fi]
        mouth = 0 if a < 0.12 else 1 if a < 0.3 else 2 if a < 0.55 else 3 if a < 0.8 else 4
        bl = 0
        for b in blinks:
            dt = ts - b
            if 0 <= dt < 0.16:
                bl = [1, 3, 3, 2, 1][min(4, int(dt / 0.033))]
        bob = 6 * math.sin(ts * 2.2)
        hx, hy = (W - HW) // 2, int(HERO_Y + bob)
        frame.alpha_composite(hero_aura(), (hx - 150, hy - 150 + 40))
        frame.alpha_composite(hero_sprite(bl, mouth), (hx, hy))
        frame.alpha_composite(name_tag(), (W // 2 + 140, HERO_Y + 470))
        # sahna
        if ts < starts[-1] + durs[-1]:
            objs[seg].draw(frame, local, durs[seg], words_all[seg])
            draw_caption(frame, words_all[seg], local)
        else:  # outro: kvest qoladi + konfetti + matn
            objs[-1].draw(frame, local, durs[-1], [])
            ot = ts - (starts[-1] + durs[-1])
            d = ImageDraw.Draw(frame)
            for x, y, vx, vy, col, ph in conf:
                yy = y + vy * ot
                xx = x + vx * ot + 20 * math.sin(ot * 4 + ph)
                d.rectangle((xx, yy, xx + 14, yy + 22), fill=col)
            paste_scaled(frame, outro_img(), W / 2, CAP_Y + 55, pop(ot, 0.3))
        # o'tish chaqnashi
        for st in starts[1:]:
            dt = ts - st
            if 0 <= dt < 0.12:
                frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(110 * (1 - dt / 0.12)))))
        # glitch (birinchi 0.4 s)
        if ts < 0.4 and fi % 2 == 0:
            arr = np.array(frame)
            for _ in range(6):
                y = rnd.randrange(0, H - 80)
                hgt = rnd.randrange(20, 80)
                arr[y:y + hgt, :, 0] = np.roll(arr[y:y + hgt, :, 0], rnd.randrange(-60, 60), axis=1)
            frame = Image.fromarray(arr)
        frame.alpha_composite(top, (0, 0))
        # kamera silkinishi
        sh = 0
        for s in shakes:
            dt = ts - s
            if 0 <= dt < 0.3:
                sh = max(sh, 22 * (1 - dt / 0.3))
        rgb = frame.convert("RGB")
        if sh:
            ox, oy = int(sh * math.sin(fi * 2.1)), int(sh * math.cos(fi * 1.7))
            z = rgb.resize((int(W * 1.04), int(H * 1.04)), Image.BILINEAR)
            rgb = z.crop((int(W * 0.02) + ox, int(H * 0.02) + oy, int(W * 0.02) + ox + W, int(H * 0.02) + oy + H))
        ff.stdin.write(rgb.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg video xatosi")

    # --- ovoz miks ---
    n = int(total * SR) + SR
    vox = np.zeros(n)
    fx = np.zeros(n)
    for i, v in enumerate(voices):
        if v is not None:
            put(vox, v * 1.0, starts[i] + 0.0)
        put(fx, sfx(objs[i].sound), max(0, starts[i] - 0.05))
    for s in shakes:
        if s > 0.1:
            put(fx, sfx("impact") * 0.7, s)
    put(fx, sfx("levelup"), starts[-1] + 0.4 + durs[-1] * objs[-1].lvl)
    mus_p = tmp / "m.wav"
    mv.music(mus_p, total)
    with wave.open(str(mus_p)) as w:
        mus = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    music = np.zeros(n)
    music[: len(mus)] = mus
    env = np.convolve(np.abs(vox), np.ones(4410) / 4410, "same")
    duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
    mix = vox * 1.1 + fx * 0.8 + music * 0.38 * duck
    mix = mix[: int(total * SR)]
    mix = np.tanh(mix * 1.2) * 0.9
    wav = tmp / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.stem + ".part.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(part)])
    if r.returncode != 0:
        raise SystemExit("ffmpeg audio xatosi")
    part.rename(out)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"seconds": round(total, 1), "voice": all(v is not None for v in voices), "day": day}


@lru_cache(maxsize=None)
def outro_img():
    im = Image.new("RGBA", (1000, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 20, 940, 180), radius=40, fill=FIRE + (255,))
    d.text((500, 72), "SAQLAB QO'Y", font=OSW(64), fill=INK, anchor="mm")
    d.text((500, 138), "ertaga — 3-kun kvesti", font=RUB(38, 700), fill=INK, anchor="mm")
    return im


def load(sid):
    for s in json.loads((HERE / "hero_scripts.json").read_text(encoding="utf-8")):
        if s["id"] == sid:
            return s
    raise SystemExit(f"{sid} topilmadi")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--frames", help="faqat shu soniyalardagi kadrlarni PNG qilib saqlash, masalan 1,5,9")
    a = ap.parse_args()
    print(render(load(a.id), a.out, voice=not a.no_voice))
