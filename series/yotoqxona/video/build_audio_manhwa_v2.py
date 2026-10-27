"""Manhwa 2-qism uchun jiddiy, qorong'i ovoz dizayni (24 s): pad, fortepiano, yurak urishi, soat, zarbalar, riser."""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

SR, DUR = 44100, 24.0
N = int(SR * DUR); OUT = sys.argv[1] if len(sys.argv) > 1 else "ep02_manhwa_audio.wav"
rng = np.random.default_rng(11)
music = np.zeros(N); fx = np.zeros(N)

def put(buf, t, sig, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    j = min(N, i + len(sig)); buf[i:j] += g * sig[: j - i]
def tt(d): return np.arange(int(d * SR)) / SR
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lpf(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hpf(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def bpf(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)

# ---------- pad (a-minor, qorong'i) ----------
def saw(f, t): return 2 * ((f * t) % 1) - 1
t_all = tt(DUR)
def pad(freqs, gain):
    s = np.zeros(N)
    for f in freqs:
        for det in (-0.35, 0.0, 0.35):
            s += saw(f * (1 + det / 100), t_all) / (3 * len(freqs))
    return lpf(s, 520, 3) * gain
swell = 0.55 + 0.45 * np.sin(2 * np.pi * t_all / 8 - 1.2)
music += pad([55, 110, 164.8, 220], 1.0) * swell * 0.55
tens = np.clip((t_all - 8) / 2, 0, 1) * np.clip((24 - t_all) / 4, 0, 1)        # 8-12 s: dissonans (Bb)
music += pad([233.1, 349.2], 1.0) * tens * 0.22
music += pad([73.4, 110.0, 130.8], 1.0) * np.clip((t_all - 16) / 3, 0, 1) * 0.35   # 16 s dan: kuchayadi

# ---------- fortepiano (siyrak, sovuq) ----------
def piano(f, d=1.6):
    t = tt(d); s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) * np.exp(-3 * t) + 0.2 * np.sin(6 * np.pi * f * t) * np.exp(-6 * t))
    return s * np.minimum(t / 0.004, 1) * np.exp(-2.4 * t)
melody = [(0.5, 69), (1.6, 72), (2.7, 76), (3.5, 74),
          (4.9, 69), (6.4, 68), (7.5, 64),
          (8.6, 70), (9.4, 69), (10.2, 70), (11.0, 69),
          (12.6, 72), (13.8, 71), (15.0, 69),
          (16.4, 69), (17.2, 72), (18.0, 76), (18.8, 77), (19.4, 76),
          (21.2, 57), (22.8, 52)]
for t0, m in melody:
    put(music, t0, piano(mtof(m)), 0.30)
    put(music, t0, piano(mtof(m - 12)), 0.10)

# ---------- zarbalar ----------
def boom(d=2.2, f0=90, f1=30):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    n = lpf(rng.standard_normal(len(t)), 600) * np.exp(-t * 6) * 1.2
    return s + n
def slam():
    t = tt(0.9); n = hpf(rng.standard_normal(len(t)), 300) * np.exp(-t * 14) * 1.4
    w = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 7)
    return n + 1.4 * w
def thump(f=58, d=0.28):
    t = tt(d); return np.sin(2 * np.pi * (f + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 15)
def tick(f=1800, d=0.05):
    t = tt(d); return hpf(rng.standard_normal(len(t)), 900) * np.exp(-t * 90) * 0.8 + 0.3 * np.sin(2 * np.pi * f * t) * np.exp(-t * 120)
def typec():
    t = tt(0.018); return hpf(rng.standard_normal(len(t)), 2500) * np.exp(-t * 180)
def pluckhit(f=880):
    t = tt(0.5); return np.sin(2 * np.pi * f * t) * np.exp(-t * 9) * 0.3 + 0.2 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 12)

# sahna boshlari (jim urg'u)
for t0 in (0.0, 8.0, 12.0, 16.0): put(fx, t0, boom(1.4, 70, 38), 0.35)
# 1-sahna: qog'oz (ijara xabarnomasi) paydo bo'lishi
put(fx, 0.5, hpf(rng.standard_normal(int(0.25 * SR)), 1500) * np.exp(-tt(0.25) * 12), 0.5)
put(fx, 1.7, slam(), 0.35)
# 2-sahna: eshik "DAN!"
put(fx, 4.1, slam(), 0.95); put(fx, 4.1, boom(2.4, 100, 28), 0.9)
# 3-sahna: telefon tebranishi "BZZT"
for p in range(3):
    t = tt(0.22); s_ = np.sign(np.sin(2 * np.pi * 160 * t)) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * t)))
    put(fx, 8.15 + p * 0.3, lpf(s_, 1200) * np.exp(-t * 5) * 0.55, 0.8)
# 4-sahna: hisob satrlari + jami + KERAK (og'ir zarba)
for t0, f_ in [(12.3, 1100), (12.9, 1300), (13.5, 700)]: put(fx, t0, pluckhit(f_), 0.7)
put(fx, 14.1, boom(1.6, 80, 34), 0.8); put(fx, 14.1, pluckhit(1500), 0.6)
put(fx, 14.9, boom(2.2, 70, 26), 1.0); put(fx, 14.9, slam(), 0.55)
# yurak urishi (10 s dan, tezlashadi)
tb = 10.0; bpm = 62
while tb < 20.0:
    put(fx, tb, thump(58), 0.85); put(fx, tb + 0.19, thump(50), 0.55)
    tb += 60 / bpm; bpm += 3.2
# pufaklar
for t0 in (5.9, 9.3, 17.0): put(fx, t0, pluckhit(560), 0.5)
# yozuv mashinkasi (narratsiya)
for t0, n in [(0.3, 24), (1.2, 55), (4.9, 26), (8.2, 25), (15.0, 28), (18.0, 36)]:
    for k in range(n): put(fx, t0 + k / 38.0, typec(), 0.22)
# 16-20 s: riser
tr = tt(3.6); fr = 110 * 2 ** (tr / 3.6 * 2.2)
rs = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.25 + lpf(rng.standard_normal(len(tr)), 4000) * (tr / 3.6) ** 2 * 0.5
put(fx, 16.0, rs * (tr / 3.6) ** 1.5, 0.55)
# 19.6-20.1 to'liq sukunat, so'ng eshik taqillashi
def knock():
    t = tt(0.5); return (np.sin(2 * np.pi * 85 * t) * np.exp(-t * 14) + hpf(rng.standard_normal(len(t)), 500) * np.exp(-t * 60) * 0.9)
for k0 in (20.2, 20.9, 21.6):
    put(fx, k0, knock(), 1.3); put(fx, k0, boom(1.2, 70, 40), 0.5)
put(fx, 22.1, boom(3.0, 90, 26), 1.0); put(fx, 22.1, slam(), 0.7)       # "IJARA — BUGUN!"
put(fx, 22.8, pluckhit(330), 0.7)
dip = np.ones(N); dip[int(19.6 * SR):int(20.1 * SR)] = 0.0
music *= dip; fx[int(19.62 * SR):int(20.1 * SR)] *= 0.04

# ---------- reverb + miks ----------
ir_t = tt(1.4); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2); ir = lpf(ir, 3500)
wet = fftconvolve(music, ir)[:N] * 0.018 + fftconvolve(fx, ir)[:N] * 0.010
mix = music * 0.9 + fx + wet
fade = np.minimum(1, np.minimum(np.arange(N) / (0.15 * SR), (DUR - np.arange(N) / SR) / 1.0))
mix = np.tanh(mix * 0.9) * fade
mix = mix / np.abs(mix).max() * 0.92
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16)); print("tayyor:", OUT)
