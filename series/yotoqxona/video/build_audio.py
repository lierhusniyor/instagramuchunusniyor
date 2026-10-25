"""YOTOQXONA 1-qism uchun ovoz: lo-fi musiqa + video bilan sinxron effektlar + multfilm "gapirish" tovushi."""
import re, sys
import numpy as np
from scipy.io import wavfile

SR = 44100
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
OUT = sys.argv[1] if len(sys.argv) > 1 else "ep01_audio.wav"

music = np.zeros(N); sfx = np.zeros(N); voice = np.zeros(N)

def put(buf, t, sig, g=1.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    j = min(N, i + len(sig)); buf[i:j] += g * sig[: j - i]

def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

# ---------- asboblar ----------
def epiano(f, d=0.6):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-4 * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-6 * t)
    return s * np.minimum(t / 0.006, 1) * np.exp(-4.2 * t)
def bass(f, d=0.5):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.minimum(t / 0.01, 1) * np.exp(-4 * t)
def kick():
    t = tt(0.22); f = 45 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16)
def snare():
    t = tt(0.2); return (rng.standard_normal(len(t)) * 0.7 + np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 24)
def hat():
    t = tt(0.06); n = rng.standard_normal(len(t)); return np.diff(n, prepend=0) * np.exp(-t * 70)

# ---------- musiqa (104 BPM, C major: Cmaj7-Am7-Fmaj7-G7) ----------
BPM = 104; beat = 60 / BPM; bar = 4 * beat
chords = [([60, 64, 67, 71], 36), ([57, 60, 64, 67], 33), ([53, 57, 60, 64], 41), ([55, 59, 62, 65], 43)]
b = 0
while b * bar < DUR:
    notes, root = chords[b % 4]; t0 = b * bar
    for e in range(8):                       # sakkizlik arpedjio
        put(music, t0 + e * beat / 2, epiano(mtof(notes[[0, 1, 2, 3, 2, 1, 2, 3][e]] + (12 if e % 4 == 3 else 0)), 0.5), 0.22)
    put(music, t0, epiano(mtof(notes[0] - 12), 1.2), 0.18)
    put(music, t0, bass(mtof(root), 0.9), 0.55); put(music, t0 + 2 * beat, bass(mtof(root), 0.5), 0.45)
    put(music, t0 + 2.5 * beat, bass(mtof(root + 7), 0.3), 0.3)
    for k in (0, 2): put(music, t0 + k * beat, kick(), 0.9)
    put(music, t0 + 2.5 * beat, kick(), 0.5)
    for k in (1, 3): put(music, t0 + k * beat, snare(), 0.35)
    for e in range(8): put(music, t0 + e * beat / 2, hat(), 0.18 if e % 2 == 0 else 0.1)
    b += 1

# ---------- effektlar ----------
def pop(f0=420, f1=950, d=0.09):
    t = tt(d); f = f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
def whoosh(d=0.28):
    t = tt(d); n = lp(rng.standard_normal(len(t)), 25)
    return n * np.sin(np.pi * t / d) ** 2 * 3
def bell(f, d=0.6):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t)) * np.exp(-t * 6)
def wah(f, d, vib=5.5):
    t = tt(d); ph = 2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * vib * t)
    s = np.sign(np.sin(ph)) * 0.5 + 0.5 * np.sin(ph)
    return lp(s, 6) * np.minimum(t / 0.03, 1) * np.exp(-t * 1.6)

SCENE_T = [0.0, 4.0, 8.0, 12.0]
for t in SCENE_T:
    put(sfx, t, pop(), 0.8)
    if t > 0: put(sfx, t - 0.22, whoosh(), 0.35)

# 2-sahna: kuya (5.0-7.2 s) va "sad trombone"
tm = tt(2.2); trem = 0.55 + 0.45 * np.sin(2 * np.pi * 26 * tm)
buzz = lp(np.sign(np.sin(2 * np.pi * (170 + 25 * np.sin(2 * np.pi * 1.7 * tm)) * tm)), 4) * trem
buzz *= np.minimum(tm / 0.2, 1) * np.minimum((2.2 - tm) / 0.5, 1)
put(sfx, 5.0, buzz, 0.28)
for i, (m, d) in enumerate([(58, 0.32), (57, 0.32), (56, 0.32), (55, 1.0)]):
    put(sfx, 5.45 + i * 0.34, wah(mtof(m), d, 5.5 + i), 0.55)
# 3-sahna: qog'ozchalar chiqishi
for i in range(6): put(sfx, 8.15 + 0.15 * i, bell(mtof(72 + [0, 4, 7, 9, 12, 16][i]), 0.35), 0.35)
# 4-sahna: quvnoq arpedjio + CTA qo'ng'irog'i
for i, m in enumerate([72, 76, 79, 84]): put(sfx, 12.05 + 0.09 * i, bell(mtof(m), 0.5), 0.4)
put(sfx, 13.4, bell(1318, 0.9), 0.5); put(sfx, 13.4, pop(600, 1200), 0.4)

# ---------- multfilm "gapirish" (matn bilan sinxron) ----------
TEXTS = [(0.35, "Men Jahongir. 22 yoshdaman."), (4.35, "Ish yo'q. Pul yo'q."), (8.35, "Lekin rejam bor."), (12.3, "Hammasi keyingi oyda yaxshi bo'ladi.")]
BASE = [210, 180, 235, 250]
def syllables(word):
    if word.isdigit(): return 3
    return max(1, len(re.findall(r"[aeiou]", word.lower())))
def blip(f, d=0.085):
    t = tt(d); s = sum(np.sin(2 * np.pi * k * f * t) / k for k in range(1, 7))
    return lp(s, 7) * np.minimum(t / 0.006, 1) * np.exp(-t * 16)
for si, (t0, text) in enumerate(TEXTS):
    t = t0; words = re.findall(r"[\w']+", text); total = sum(syllables(w) for w in words); k = 0
    for w in words:
        for _ in range(syllables(w)):
            f = BASE[si] * (1 + 0.18 * np.sin(k * 0.9) + rng.uniform(-0.06, 0.06)) * (1 + 0.1 * k / max(total, 1))
            put(voice, t, blip(f), 0.5); t += 0.118; k += 1
        t += 0.07

mix = 0.55 * music + 0.9 * sfx + 0.7 * voice
fade = np.minimum(1, (DUR - np.arange(N) / SR) / 0.5)
mix = np.tanh(mix * 1.1) * fade
mix = mix / max(1e-9, np.abs(mix).max()) * 0.9
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16))
print("tayyor:", OUT)
