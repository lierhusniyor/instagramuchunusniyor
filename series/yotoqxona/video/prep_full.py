"""To'liq bo'yli qahramonlarni oq fondan ajratadi: prep_full.py (rasm yo'llari ichkarida)."""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage
B = "/mnt/user-data/attachments/db4b018d-bcb0-595e-b931-6a1d8b5fabb3"
SRC = {"full_jahongir": "body_noswoosh.png", "full_malika": f"{B}/39a0b007-image.png", "full_dilnoza": f"{B}/0a11955d-image.png"}

def cut(path):
    im = Image.open(path).convert("RGB"); a = np.asarray(im).astype(int); Hh = a.shape[0]
    white = a.min(axis=2) > 236
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border)); bg_all = bg
    lab2, n2 = ndimage.label(white & ~bg)
    for k in range(1, n2 + 1):
        m = lab2 == k; area = m.sum()
        cy, cx = ndimage.center_of_mass(m); cy /= Hh
        xs_ = np.where(~bg_all)[1]; mid = (xs_.min() + xs_.max()) / 2; wid = xs_.max() - xs_.min()
        side = abs(cx - mid) / wid
        if (0.5 < cy < 0.9 and area < 40000) or (cy < 0.2 and area < 6000 and side > 0.14):
            bg[m] = True
    al = Image.fromarray(np.where(bg, 0, 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA"); out.putalpha(al)
    return out.crop(al.point(lambda v: 255 if v > 20 else 0).getbbox())

for k, p in SRC.items():
    c = cut(p); c.save(f"assets/{k}.png"); print(k, c.size)
room = Image.open(f"{B}/cf4a2a16-image.png").convert("RGB").filter(ImageFilter.GaussianBlur(5))
ImageEnhance.Brightness(ImageEnhance.Color(room).enhance(0.8)).enhance(0.72).save("assets/room_bg.png")
