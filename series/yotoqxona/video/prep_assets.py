"""Rasmlardan oq fonni olib tashlab, kerakli qismlarni kesadi."""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC_BODY, SRC_SHEET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

def white_mask(img):
    return np.asarray(img.convert("RGB")).astype(int).min(axis=2) > 235

def cutout(img):
    """Chekkaga ulangan oq fonni shaffof qiladi."""
    white = white_mask(img)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    alpha = Image.fromarray(np.where(bg, 0, 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = img.convert("RGBA"); out.putalpha(alpha)
    return out

def clean_pockets(rgba, frac):
    """Soch orasidagi yopiq oq cho'ntaklarni (tepa `frac` qismida) shaffof qiladi."""
    rgb = rgba.convert("RGB")
    a = np.asarray(rgba)[:, :, 3].copy()
    white = white_mask(rgb) & (a > 0)
    lab, n = ndimage.label(white)
    h = a.shape[0]
    for k in range(1, n + 1):
        yy, _ = np.where(lab == k)
        if yy.size < 4000 and yy.mean() < frac * h:
            a[lab == k] = 0
    out = rgba.copy(); out.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6)))
    return out

body = cutout(Image.open(SRC_BODY)).crop((170, 0, 770, 930))
clean_pockets(body, 0.09).save(f"{OUT}/body.png")

sheet = cutout(Image.open(SRC_SHEET))
al = np.asarray(sheet)[:, :, 3] > 128
al = ndimage.binary_closing(al, iterations=3)
lab, n = ndimage.label(al)
sizes = ndimage.sum(al, lab, range(1, n + 1))
top = np.argsort(sizes)[::-1][:6] + 1
boxes = []
for k in top:
    ys, xs = np.where(lab == k)
    boxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
boxes.sort(key=lambda b: (b[1] + b[3]) / 2)
rows = [sorted(boxes[i:i + 2], key=lambda b: b[0]) for i in (0, 2, 4)]
ordered = [b for r in rows for b in r]
names = ["happy", "shock", "angry", "sad", "smirk", "tired"]
for nm, b in zip(names, ordered):
    clean_pockets(sheet.crop(b), 0.33).save(f"{OUT}/{nm}.png")
    print(nm, b)
