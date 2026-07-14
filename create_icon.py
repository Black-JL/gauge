#!/usr/bin/env python3
"""Generate a minimal Gauge app icon (dark face, white dial) and build Gauge.icns."""

import math
import os
import subprocess
from PIL import Image, ImageDraw

SIZE = 1024
HERE = os.path.dirname(os.path.abspath(__file__))

INK = (255, 255, 255)
DIM = (90, 90, 90)
RED = (255, 59, 48)
BG = (10, 10, 10)

START, SWEEP = 135.0, 270.0          # matches the UI: 270° sweep, gap at bottom


def ang(f):
    return START + f * SWEEP


def pt(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def main():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # rounded-square dark face (macOS-style)
    pad = int(SIZE * 0.06)
    d.rounded_rectangle([pad, pad, SIZE - pad, SIZE - pad],
                        radius=int(SIZE * 0.22), fill=BG,
                        outline=(38, 38, 38), width=int(SIZE * 0.006))

    cx = cy = SIZE // 2
    R = SIZE * 0.33

    # main arc
    bbox = [cx - R, cy - R, cx + R, cy + R]
    d.arc(bbox, ang(0), ang(1), fill=(70, 70, 70), width=int(SIZE * 0.012))

    # red redline near the top of the scale
    d.arc(bbox, ang(0.85), ang(1), fill=RED, width=int(SIZE * 0.028))

    # major ticks
    for i in range(11):
        f = i / 10.0
        col = RED if f >= 0.85 else INK
        p0 = pt(cx, cy, R * 1.02, ang(f))
        p1 = pt(cx, cy, R * 0.86, ang(f))
        d.line([p0, p1], fill=col, width=int(SIZE * 0.010))

    # needle pointing to ~72%
    f = 0.72
    tip = pt(cx, cy, R * 0.9, ang(f))
    tail = pt(cx, cy, R * 0.18, ang(f) + 180)
    d.line([tail, tip], fill=INK, width=int(SIZE * 0.016))
    # red needle tip
    mid = pt(cx, cy, R * 0.66, ang(f))
    d.line([mid, tip], fill=RED, width=int(SIZE * 0.016))
    d.ellipse([cx - SIZE * 0.028, cy - SIZE * 0.028,
               cx + SIZE * 0.028, cy + SIZE * 0.028], fill=(232, 232, 232))

    png = os.path.join(HERE, "icon_1024.png")
    img.save(png)
    print("wrote", png)

    # build .icns
    iconset = os.path.join(HERE, "Gauge.iconset")
    os.makedirs(iconset, exist_ok=True)
    specs = [(16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2),
             (256, 1), (256, 2), (512, 1), (512, 2)]
    for base, scale in specs:
        px = base * scale
        name = "icon_%dx%d%s.png" % (base, base, "@2x" if scale == 2 else "")
        img.resize((px, px), Image.LANCZOS).save(os.path.join(iconset, name))
    icns = os.path.join(HERE, "Gauge.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns], check=True)
    print("wrote", icns)


if __name__ == "__main__":
    main()
