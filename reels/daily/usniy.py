"""'Usniy' vektor qahramoni: kanal maskoti. PIL bilan chiziladi (tashqi rasm kerak emas).

sprites() -> {(mouth, eyes, arm): RGBA rasm 900x1100}
mouth: closed | open | wide;  eyes: open | closed;  arm: phone | point
"""
from PIL import Image, ImageDraw

W, H = 900, 1100
S = 2  # sifat uchun 2x chizib, keyin kichraytiriladi

SKIN = "#f2c29b"
SKIN_DARK = "#e0a77f"
HAIR = "#2b1d3a"
HOODIE = "#ff8a3d"
HOODIE_DARK = "#e86f22"
PHONE = "#7c3aed"
SCREEN = "#c4b5fd"
INK = "#2b1d3a"
MOUTH = "#5a1a2a"
TONGUE = "#ff6b81"
CHEEK = "#f6a49a"


def _b(box):
    return [v * S for v in box]


def _draw(mouth, eyes, arm):
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # tana (xudi)
    d.rounded_rectangle(_b((170, 700, 730, 1160)), radius=170 * S, fill=HOODIE)
    d.polygon(_b((360, 700, 450, 800, 540, 700)), fill=HOODIE_DARK)  # yoqa
    d.line(_b((405, 760, 395, 880)), fill="#fff3e6", width=10 * S)  # ip
    d.line(_b((495, 760, 505, 880)), fill="#fff3e6", width=10 * S)
    d.ellipse(_b((382, 870, 408, 896)), fill="#fff3e6")
    d.ellipse(_b((492, 870, 518, 896)), fill="#fff3e6")
    d.rounded_rectangle(_b((330, 960, 570, 1060)), radius=30 * S, fill=HOODIE_DARK)  # cho'ntak

    # bo'yin
    d.rectangle(_b((400, 620, 500, 720)), fill=SKIN_DARK)

    # quloqlar
    d.ellipse(_b((190, 390, 270, 510)), fill=SKIN)
    d.ellipse(_b((630, 390, 710, 510)), fill=SKIN)

    # bosh
    d.ellipse(_b((220, 190, 680, 690)), fill=SKIN)

    # soch
    d.chord(_b((212, 170, 688, 500)), 180, 360, fill=HAIR)
    for x0 in (250, 330, 410, 490, 570):  # chakka-peshona tolalari
        d.pieslice(_b((x0, 290, x0 + 90, 380)), 0, 180, fill=HAIR)
    d.ellipse(_b((330, 120, 560, 270)), fill=HAIR)
    d.ellipse(_b((260, 160, 420, 290)), fill=HAIR)
    d.ellipse(_b((480, 150, 640, 300)), fill=HAIR)
    d.ellipse(_b((212, 250, 290, 400)), fill=HAIR)  # chakka
    d.ellipse(_b((610, 250, 688, 400)), fill=HAIR)


    # ko'zlar
    if eyes == "open":
        for cx in (365, 535):
            d.ellipse(_b((cx - 48, 395, cx + 48, 505)), fill="white")
            d.ellipse(_b((cx - 28, 425, cx + 28, 485)), fill=INK)
            d.ellipse(_b((cx - 14, 432, cx + 4, 450)), fill="white")
    else:
        for cx in (365, 535):
            d.arc(_b((cx - 44, 420, cx + 44, 480)), 10, 170, fill=INK, width=10 * S)

    # yonoqlar
    d.ellipse(_b((285, 515, 345, 555)), fill=CHEEK)
    d.ellipse(_b((555, 515, 615, 555)), fill=CHEEK)

    # og'iz
    if mouth == "closed":
        d.arc(_b((395, 535, 505, 600)), 20, 160, fill=MOUTH, width=10 * S)
    else:
        box = (410, 550, 490, 605) if mouth == "open" else (395, 540, 505, 630)
        d.ellipse(_b(box), fill=MOUTH)
        tb = (box[0] + 14, (box[1] + box[3]) // 2 + 2, box[2] - 14, box[3] - 2)
        d.ellipse(_b(tb), fill=TONGUE)

    # qo'llar
    if arm == "point":
        d.line(_b((250, 790, 150, 560)), fill=HOODIE, width=100 * S)
        d.ellipse(_b((200, 740, 300, 840)), fill=HOODIE)
        # ochiq kaft (salom)
        for fx, top in ((108, 440), (138, 418), (168, 424), (196, 448)):
            d.rounded_rectangle(_b((fx - 15, top, fx + 15, 560)), radius=15 * S, fill=SKIN)
        d.ellipse(_b((96, 500, 214, 610)), fill=SKIN)
        d.line(_b((190, 585, 228, 548)), fill=SKIN, width=32 * S)
        d.ellipse(_b((212, 530, 244, 562)), fill=SKIN)
    # telefon (doim o'ng qo'lda)
    d.rounded_rectangle(_b((600, 690, 740, 920)), radius=22 * S, fill=PHONE)
    d.rounded_rectangle(_b((614, 708, 726, 900)), radius=12 * S, fill=SCREEN)
    # ekranda yurakcha
    d.ellipse(_b((641, 770, 673, 802)), fill="#ff4d6d")
    d.ellipse(_b((667, 770, 699, 802)), fill="#ff4d6d")
    d.polygon(_b((643, 792, 697, 792, 670, 828)), fill="#ff4d6d")
    d.ellipse(_b((610, 860, 700, 950)), fill=SKIN)  # kaft

    return img.resize((W, H), Image.LANCZOS)


def sprites():
    out = {}
    for mouth in ("closed", "open", "wide"):
        for eyes in ("open", "closed"):
            for arm in ("phone", "point"):
                out[(mouth, eyes, arm)] = _draw(mouth, eyes, arm)
    return out


if __name__ == "__main__":
    _draw("open", "open", "point").save("usniy_preview.png")
