"""3x2 kayfiyat varag'idan 6 ta yuzni kesadi: prep_faces.py <varaq.png> <prefiks> <chiqish papkasi>"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC, PFX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NAMES = ["happy", "shock", "angry", "sad", "smirk", "tired"]
im = Image.open(SRC).convert("RGB")
W, H = im.size
pw, ph, INSET = W // 3, H // 2, 6

def cutout(p):
    a = np.asarray(p).astype(int)
    white = a.min(axis=2) > 232
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    # soch orasidagi oq cho'ntaklar: markazi yuz (teri) chegarasidan tashqarida bo'lsa olib tashlanadi
    skin = (a[:, :, 0] > 190) & (a[:, :, 1] > 140) & (a[:, :, 2] > 110) & (a[:, :, 0] - a[:, :, 2] > 25)
    ys, xs = np.where(skin[: int(0.75 * a.shape[0])])
    x0, x1, y0 = np.percentile(xs, 1), np.percentile(xs, 99), np.percentile(ys, 1)
    H_ = a.shape[0]
    by, bx = np.where(skin[int(0.6 * H_): int(0.9 * H_)])
    nx0, nx1 = (np.percentile(bx, 2), np.percentile(bx, 98)) if bx.size else (x0, x1)
    lab2, n2 = ndimage.label(white & ~bg)
    for k in range(1, n2 + 1):
        m = lab2 == k
        if m.sum() > 8000: continue
        cy, cx = ndimage.center_of_mass(m)
        if cx < x0 or cx > x1 or cy < y0 or (cy > 0.6 * H_ and (cx < nx0 or cx > nx1)):
            bg[m] = True
    al = Image.fromarray(np.where(bg, 0, 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = p.convert("RGBA"); out.putalpha(al)
    bbox = al.point(lambda v: 255 if v > 20 else 0).getbbox()
    return out.crop(bbox)

for i, nm in enumerate(NAMES):
    r, c = divmod(i, 3)
    p = im.crop((c * pw + INSET, r * ph + INSET, (c + 1) * pw - INSET, (r + 1) * ph - INSET))
    cutout(p).save(f"{OUT}/{PFX}_{nm}.png")
print("ok", PFX)
