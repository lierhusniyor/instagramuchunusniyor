"""Bitta ssenariydan 1080x1920 Reels: Usniy qahramoni + matn pufagi + ovoz + musiqa.

python3 make_video.py --id d01 --out out/d01.mp4 [--no-voice]
Ovoz: edge-tts (uz-UZ-SardorNeural). O'rnatilmagan bo'lsa yoki --no-voice, ovozsiz (musiqa bilan).
"""
import argparse
import json
import math
import random
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import usniy

HERE = Path(__file__).parent
W, H, FPS = 1080, 1920, 30
FONT = str(HERE / "fonts" / "Poppins-Bold.ttf")
VOICE = "uz-UZ-SardorNeural"
CTA = "Foydali bo'lsa, obuna bo'ling!"
HANDLE = "@usniy_or"
GAP = 0.35  # gaplar orasidagi pauza (s)
CHAR_X, CHAR_Y = 90, 860


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
    return 0.6 + 0.42 * len(text.split())


# ---------- musiqa ----------
def music(path, seconds, sr=44100):
    """Yengil lo-fi fon: akkordlar + baraban. Mualliflik huquqi muammosi yo'q."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    bpm = 96
    beat = 60 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    out = np.zeros(n)
    bar = beat * 4
    for i in range(int(seconds / bar) + 1):
        s, e = int(i * bar * sr), min(n, int((i + 1) * bar * sr))
        if s >= n:
            break
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt / 0.3) * np.exp(-tt / 3.0)
        for m in chords[i % 4]:
            f = 440 * 2 ** ((m - 69) / 12)
            out[s:e] += 0.09 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
        bass = 440 * 2 ** ((chords[i % 4][0] - 12 - 69) / 12)
        out[s:e] += 0.12 * env * np.sin(2 * np.pi * bass * tt)
    rng = np.random.default_rng(1)
    for k in range(int(seconds / beat) + 1):
        s = int(k * beat * sr)
        if s >= n:
            break
        L = min(int(0.25 * sr), n - s)
        tt = np.arange(L) / sr
        kick = np.sin(2 * np.pi * (50 + 80 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
        out[s:s + L] += 0.35 * kick
        h = s + int(beat / 2 * sr)
        if h < n:
            L = min(int(0.05 * sr), n - h)
            out[h:h + L] += 0.05 * rng.standard_normal(L) * np.exp(-np.arange(L) / sr * 80)
    fade = int(1.0 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    data = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


# ---------- grafika ----------
def font(size):
    return ImageFont.truetype(FONT, size)


def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def background():
    """Fon 1080x2300 (sekin suriladi)."""
    bh = H + 380
    top, bot = np.array([76, 29, 149]), np.array([24, 8, 52])
    g = np.linspace(0, 1, bh)[:, None]
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    img = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1).reshape(bh, W, 3))
    blobs = Image.new("RGBA", (W, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(blobs)
    rnd = random.Random(7)
    for _ in range(9):
        x, y, r = rnd.randint(-100, W), rnd.randint(0, bh), rnd.randint(120, 260)
        col = rnd.choice([(255, 138, 61, 70), (167, 139, 250, 80), (236, 72, 153, 60)])
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    blobs = blobs.filter(ImageFilter.GaussianBlur(60))
    img = img.convert("RGBA")
    img.alpha_composite(blobs)
    # pastki "pol" yorug'ligi
    floor = Image.new("RGBA", (W, bh), (0, 0, 0, 0))
    ImageDraw.Draw(floor).ellipse((90, bh - 260, 990, bh + 60), fill=(255, 138, 61, 60))
    img.alpha_composite(floor.filter(ImageFilter.GaussianBlur(40)))
    return img


def hook_layer(text):
    layer = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(96)
    lines = wrap(d, text.upper(), f, W - 140)
    if len(lines) > 4:
        f = font(80)
        lines = wrap(d, text.upper(), f, W - 120)
    lh = int(f.size * 1.22)
    y = (760 - lh * len(lines)) // 2
    for ln in lines:
        tw = d.textlength(ln, font=f)
        x = (W - tw) / 2
        d.rounded_rectangle((x - 26, y - 6, x + tw + 26, y + lh - 4), radius=22, fill=(255, 138, 61, 255))
        d.text((x + 5, y + 5), ln, font=f, fill=(43, 29, 58, 255))
        d.text((x, y), ln, font=f, fill="white")
        y += lh
    return layer


def bubble_layer(text, idx, total, cta=False):
    layer = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(74)
    pad = 56
    maxw = W - 120 - 2 * pad
    lines = wrap(d, text, f, maxw)
    if len(lines) > 4:
        f = font(62)
        lines = wrap(d, text, f, maxw)
    lh = int(f.size * 1.28)
    bh = lh * len(lines) + 2 * pad + (70 if cta else 0)
    top = 690 - bh - 60
    fill = (255, 138, 61, 255) if cta else (255, 255, 255, 255)
    ink = "white" if cta else (43, 29, 58, 255)
    d.rounded_rectangle((70, top + 10, W - 70, top + bh + 10), radius=48, fill=(20, 6, 40, 110))
    d.rounded_rectangle((60, top, W - 60, top + bh), radius=48, fill=fill)
    d.polygon([(470, top + bh - 2), (560, top + bh - 2), (500, top + bh + 70)], fill=fill)  # dum
    y = top + pad
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=ink)
        y += lh
    if cta:
        fh = font(58)
        tw = d.textlength(HANDLE, font=fh)
        d.text(((W - tw) / 2, y + 6), HANDLE, font=fh, fill=(43, 29, 58, 255))
    if not cta and total:
        tag = f"{idx}/{total}"
        ft = font(40)
        tw = d.textlength(tag, font=ft)
        d.rounded_rectangle((W - 60 - tw - 50, top - 30, W - 80, top + 30), radius=30, fill=(124, 58, 237, 255))
        d.text((W - 60 - tw - 25, top - 26), tag, font=ft, fill="white")
    return layer


def badge_layer():
    layer = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(42)
    txt = "INSTAGRAM SIRLARI"
    tw = d.textlength(txt, font=f)
    x = (W - tw) / 2
    d.rounded_rectangle((x - 34, 40, x + tw + 34, 112), radius=36, fill=(255, 255, 255, 40))
    d.text((x, 46), txt, font=f, fill="white")
    return layer


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def render(script, out, voice=True):
    segs = [("hook", script["hook"])] + [("line", s) for s in script["lines"]] + [("cta", CTA)]
    tmp = Path(tempfile.mkdtemp())
    audio, durs = [], []
    for i, (_, text) in enumerate(segs):
        p = tmp / f"v{i}.mp3"
        if voice and tts(text, p):
            audio.append(p)
            durs.append(duration(p))
        else:
            audio.append(None)
            durs.append(estimate(text))
    starts, t = [], 0.4
    for dd in durs:
        starts.append(t)
        t += dd + GAP
    total = t + 0.6
    nlines = len(script["lines"])

    bg = background()
    sprites = usniy.sprites()
    badge = badge_layer()
    layers = []
    li = 0
    for kind, text in segs:
        if kind == "hook":
            layers.append(hook_layer(text))
        elif kind == "line":
            li += 1
            layers.append(bubble_layer(text, li, nlines))
        else:
            layers.append(bubble_layer(text, 0, 0, cta=True))

    nframes = int(total * FPS)
    silent = tmp / "silent.mp4"
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    rnd = random.Random(3)
    mouth_seq = [rnd.choice(["open", "wide", "open", "closed"]) for _ in range(nframes // 3 + 2)]
    for fi in range(nframes):
        tsec = fi / FPS
        seg = max([i for i, s in enumerate(starts) if s <= tsec] or [0])
        local = tsec - starts[seg]
        talking = starts[seg] <= tsec < starts[seg] + durs[seg] - 0.05
        offy = int(380 * fi / max(1, nframes - 1))
        frame = bg.crop((0, offy, W, offy + H))
        if segs[seg][0] != "hook":
            frame.alpha_composite(badge, (0, 120))
        lay = layers[seg]
        k = ease_out(local / 0.35)
        if segs[seg][0] == "hook":
            sc = 0.7 + 0.3 * k
            lw, lh = int(W * sc), int(lay.height * sc)
            l2 = lay.resize((lw, lh), Image.BILINEAR) if sc < 0.999 else lay
            frame.alpha_composite(l2, ((W - lw) // 2, 200 + (lay.height - lh) // 2))
        else:
            dy = int(60 * (1 - k))
            if k < 1:
                l2 = lay.copy()
                l2.putalpha(l2.getchannel("A").point(lambda a, kk=k: int(a * kk)))
            else:
                l2 = lay
            frame.alpha_composite(l2, (0, 240 + dy))
        mouth = mouth_seq[fi // 3] if talking else "closed"
        eyes = "closed" if fi % 100 in (0, 1, 2, 3) else "open"
        arm = "point" if segs[seg][0] in ("hook", "cta") else "phone"
        bob = int(10 * math.sin(tsec * 2 * math.pi / 1.6))
        frame.alpha_composite(sprites[(mouth, eyes, arm)], (CHAR_X, CHAR_Y + bob))
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg video xatosi")

    mus = tmp / "music.wav"
    music(mus, total)
    inputs, filters, labels = ["-i", str(silent), "-i", str(mus)], ["[1:a]volume=0.35[m]"], ["[m]"]
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
    return {"seconds": round(total, 1), "voice": all(audio)}


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
