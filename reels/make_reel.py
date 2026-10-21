#!/usr/bin/env python3
"""Matn slaydlaridan vertikal (1080x1920) Instagram Reel yasaydi.

Ishlatish:
    python3 make_reel.py slides.json chiqish.mp4

slides.json formati:
    {
      "slides": [
        {"text": "Birinchi gap", "seconds": 2.5},
        {"text": "Ikkinchi gap", "seconds": 3}
      ],
      "bg1": "#0f172a", "bg2": "#1e3a8a"   (ixtiyoriy)
    }
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_PATH = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient(c1, c2):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


def wrap(draw, text, font, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def render_slide(text, bg, out_path):
    img = bg.copy()
    draw = ImageDraw.Draw(img)
    size = 110
    while True:
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap(draw, text, font, W - 160)
        line_h = int(size * 1.3)
        if len(lines) * line_h <= H * 0.6 or size <= 50:
            break
        size -= 6
    y = (H - len(lines) * line_h) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (W - w) / 2
        draw.text((x + 4, y + 4), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_h
    img.save(out_path)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2]).resolve()
    bg = gradient(
        hex_to_rgb(config.get("bg1", "#0f172a")),
        hex_to_rgb(config.get("bg2", "#1e3a8a")),
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        concat = []
        for i, slide in enumerate(config["slides"]):
            png = tmp / f"s{i:03d}.png"
            render_slide(slide["text"], bg, png)
            concat.append(f"file '{png}'")
            concat.append(f"duration {slide.get('seconds', 3)}")
        concat.append(concat[-2])  # oxirgi kadr ffmpeg uchun takrorlanadi
        list_file = tmp / "list.txt"
        list_file.write_text("\n".join(concat), encoding="utf-8")
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-vf", f"fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-movflags", "+faststart",
                str(out),
            ],
            check=True,
        )
    print(f"Tayyor: {out}")


if __name__ == "__main__":
    main()
