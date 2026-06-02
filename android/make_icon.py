#!/usr/bin/env python3
"""Generate the AYED NETWORK MASTER PRO launcher icon + splash (real PNGs).

Dark premium telecom theme: cell tower, signal waves, and the letter A.
Run in CI (needs Pillow): python android/make_icon.py
Outputs android/icon.png (512x512) and android/presplash.png (1024x1024).
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (8, 12, 20, 255)
ACCENT = (51, 204, 255, 255)
MAST = (130, 205, 235, 255)


def _font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_logo(size):
    img = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(img)
    cx = size // 2
    top = int(size * 0.30)
    w = max(3, size // 80)
    # signal waves radiating from the top of the tower
    for k in range(1, 4):
        r = int(size * (0.10 + 0.085 * k))
        d.arc([cx - r, top - r, cx + r, top + r], 210, 330, fill=ACCENT, width=w)
    # tower: mast + two legs
    base_y = int(size * 0.76)
    apex_y = int(size * 0.40)
    d.line([cx, apex_y, cx, base_y], fill=MAST, width=max(4, size // 64))
    d.line([cx - int(size * 0.11), base_y, cx, apex_y], fill=MAST, width=max(3, size // 90))
    d.line([cx + int(size * 0.11), base_y, cx, apex_y], fill=MAST, width=max(3, size // 90))
    # cross-braces
    for f in (0.52, 0.64):
        y = int(apex_y + (base_y - apex_y) * f)
        dx = int(size * 0.11 * f)
        d.line([cx - dx, y, cx + dx, y], fill=MAST, width=max(2, size // 130))
    # big letter A
    d.text((cx, int(size * 0.60)), "A", font=_font(int(size * 0.30)),
           fill=ACCENT, anchor="mm")
    return img


def main():
    draw_logo(512).save(os.path.join(HERE, "icon.png"))

    sp = Image.new("RGBA", (1024, 1024), BG)
    sp.alpha_composite(draw_logo(560), (232, 96))
    d = ImageDraw.Draw(sp)
    d.text((512, 760), "AYED NETWORK MASTER PRO", font=_font(50),
           fill=(232, 242, 255, 255), anchor="mm")
    d.text((512, 826), "by Ayed Oraybi", font=_font(32, bold=False),
           fill=(120, 160, 190, 255), anchor="mm")
    sp.convert("RGB").save(os.path.join(HERE, "presplash.png"))
    print("Generated icon.png + presplash.png in", HERE)


if __name__ == "__main__":
    main()
