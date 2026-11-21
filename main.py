#!/usr/bin/env python3
"""Catalogue photograph of an impossible gadget: the LOOPCELL self-charging
power bank. Its USB-C cable loops out of its own top port and plugs straight
back into its own bottom port, so it charges itself forever. The screen reads
infinity percent. Beside it lies the one accessory it never needs: a wall
charger, unplugged.

Pure standard library. Renders a 1024x1024 PNG to /output/entry.png.
"""
import math
import os
import random
import struct
import zlib

W, H = 1024, 1024
OUT = os.environ.get("OUTPUT_DIR", "/output")
PATH = os.path.join(OUT, "entry.png")

# ---------------------------------------------------------------- canvas ----
img = bytearray(W * H * 3)


def px(x, y):
    return (y * W + x) * 3


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = px(x, y)
        img[i], img[i + 1], img[i + 2] = c


def blend_px(x, y, c, a):
    """Blend colour c over pixel with alpha a (0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = px(x, y)
        if a >= 1:
            img[i], img[i + 1], img[i + 2] = c
        else:
            img[i] = int(img[i] * (1 - a) + c[0] * a)
            img[i + 1] = int(img[i + 1] * (1 - a) + c[1] * a)
            img[i + 2] = int(img[i + 2] * (1 - a) + c[2] * a)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fill_rect(x0, y0, x1, y1, c, a=1.0):
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            blend_px(x, y, c, a)


def fill_ellipse(cx, cy, rx, ry, c, a=1.0):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        if y < 0 or y >= H:
            continue
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        dx = rx * math.sqrt(1 - t * t)
        for x in range(int(cx - dx), int(cx + dx) + 1):
            blend_px(x, y, c, a)


def fill_circle(cx, cy, r, c, a=1.0):
    fill_ellipse(cx, cy, r, r, c, a)


def rounded_rect(x0, y0, x1, y1, r, top_c, bot_c):
    """Filled rounded rect with a vertical gradient."""
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        c = lerp(top_c, bot_c, t)
        dy = min(y - y0, y1 - 1 - y)
        if dy < r:
            dx = r - math.sqrt(max(0, r * r - (r - dy) * (r - dy)))
            xa, xb = int(x0 + dx), int(x1 - dx)
        else:
            xa, xb = x0, x1
        row = bytes(c) * (xb - xa)
        i = px(xa, y)
        img[i:i + (xb - xa) * 3] = row


def rounded_rect_alpha(x0, y0, x1, y1, r, c, a):
    for y in range(y0, y1):
        dy = min(y - y0, y1 - 1 - y)
        if dy < r:
            dx = r - math.sqrt(max(0, r * r - (r - dy) * (r - dy)))
            xa, xb = int(x0 + dx), int(x1 - dx)
        else:
            xa, xb = x0, x1
        for x in range(xa, xb):
            blend_px(x, y, c, a)


def ring(cx, cy, rx, ry, c, w=3, a=1.0):
    """Ellipse outline by perimeter sampling."""
    steps = int(2 * math.pi * max(rx, ry) * 2)
    for s in range(steps):
        th = 2 * math.pi * s / steps
        for k in range(w):
            blend_px(int(cx + (rx - k * 0.6) * math.cos(th)),
                     int(cy + (ry - k * 0.6) * math.sin(th)), c, a)


def draw_infinity(cx, cy, r, c, w=3, a=1.0):
    """Sideways-8 glyph from two ring outlines, centred at (cx, cy)."""
    ring(cx - r, cy, r, int(r * 0.85), c, w, a)
    ring(cx + r, cy, r, int(r * 0.85), c, w, a)


# ------------------------------------------------------------- bitmap font --
# 5x7 glyphs, rows as 5-bit strings.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    " ": ["00000"] * 7,
    # infinity: two small loops side by side
    "I8": ["00000", "01010", "10101", "10101", "01010", "00000", "00000"],
}


def draw_text(x, y, s, c, scale=2, a=1.0):
    """Draw text; use '~' in the string for the infinity glyph."""
    cx = x
    for ch in s:
        g = FONT.get("I8" if ch == "~" else ch.upper())
        if g is None:
            cx += 6 * scale
            continue
        for r in range(7):
            for col in range(5):
                if g[r][col] == "1":
                    fill_rect(cx + col * scale, y + r * scale,
                              cx + (col + 1) * scale, y + (r + 1) * scale, c, a)
        cx += 6 * scale
    return cx


def text_w(s, scale=2):
    return len(s) * 6 * scale - scale


# ------------------------------------------------------------------ scene ---
# 1. Studio backdrop: soft vertical gradient, brighter centre-top.
for y in range(H):
    t = y / (H - 1)
    c = lerp((243, 244, 246), (203, 207, 212), t)
    row = bytes(c) * W
    i = px(0, y)
    img[i:i + W * 3] = row

# Gentle radial light pool behind the product.
for y in range(0, H, 2):
    for x in range(0, W, 2):
        d = math.hypot((x - 500) / 620.0, (y - 430) / 560.0)
        if d < 1:
            blend_px(x, y, (255, 255, 255), 0.10 * (1 - d))
            blend_px(x + 1, y, (255, 255, 255), 0.10 * (1 - d))
            blend_px(x, y + 1, (255, 255, 255), 0.10 * (1 - d))
            blend_px(x + 1, y + 1, (255, 255, 255), 0.10 * (1 - d))

# Floor: horizon line at y=800, slightly darker floor below.
for y in range(800, H):
    t = (y - 800) / (H - 800)
    c = lerp((196, 200, 205), (168, 173, 180), t)
    row = bytes(c) * W
    i = px(0, y)
    img[i:i + W * 3] = row
# Soft horizon glow line.
for y in range(798, 802):
    for x in range(W):
        blend_px(x, y, (255, 255, 255), 0.18)

# Vignette: darken corners a touch.
for y in range(0, H, 3):
    for x in range(0, W, 3):
        d = math.hypot((x - 512) / 720.0, (y - 512) / 720.0)
        if d > 0.75:
            a = min(0.14, (d - 0.75) * 0.45)
            for dx in range(3):
                for dy in range(3):
                    blend_px(x + dx, y + dy, (40, 44, 52), a)

# 2. Contact shadows on the floor (soft, layered ellipses).
for k in range(9):
    a = 0.05 + 0.02 * k
    fill_ellipse(500, 812, 250 - k * 14, 26 - k * 1.6, (30, 32, 38), a)
for k in range(6):
    fill_ellipse(760, 838, 90 - k * 9, 13 - k * 1.2, (30, 32, 38), 0.05 + 0.02 * k)

# ------------------------------------------------------------------- cable --
# The cable leaves the top port, loops up and right, and plugs back into the
# bottom port of the same device. Cubic bezier sampled thick.
def cubic(p0, p1, p2, p3, n=220):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] +
             3 * mt * t * t * p2[0] + t ** 3 * p3[0])
        y = (mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] +
             3 * mt * t * t * p2[1] + t ** 3 * p3[1])
        pts.append((x, y))
    return pts


cable_pts = cubic((512, 288), (560, 148), (760, 168), (700, 368)) + \
    cubic((700, 368), (660, 518), (700, 678), (596, 786))[1:]
# Cable shadow on the backdrop (offset, faint) - drawn before the cable.
for (x, y) in cable_pts[::2]:
    fill_circle(int(x) + 10, int(y) + 14, 8, (90, 94, 100), 0.10)
# Cable body: dark graphite with a lighter core line.
for (x, y) in cable_pts:
    fill_circle(int(x), int(y), 9, (38, 40, 46), 0.95)
for (x, y) in cable_pts:
    fill_circle(int(x) - 3, int(y) - 3, 3, (120, 126, 134), 0.85)

# ------------------------------------------------------------------ device --
DX0, DY0, DX1, DY1 = 392, 284, 632, 800
# Main body: brushed dark graphite, lighter at top-left (key light).
rounded_rect(DX0, DY0, DX1, DY1, 40, (66, 71, 80), (22, 24, 29))
# Brushed-metal horizontal streaks.
rng = random.Random(7)
for _ in range(2600):
    x = rng.randint(DX0 + 8, DX1 - 9)
    y = rng.randint(DY0 + 8, DY1 - 9)
    v = rng.randint(-14, 16)
    i = px(x, y)
    img[i] = max(0, min(255, img[i] + v))
    img[i + 1] = max(0, min(255, img[i + 1] + v))
    img[i + 2] = max(0, min(255, img[i + 2] + v))
# Edge highlights: key light from upper left.
for k in range(3):
    fill_rect(DX0 + 3 + k, DY0 + 40, DX0 + 4 + k, DY1 - 40, (150, 158, 168), 0.5 - k * 0.12)
for k in range(3):
    fill_rect(DX0 + 40, DY0 + 3 + k, DX1 - 40, DY0 + 4 + k, (150, 158, 168), 0.5 - k * 0.12)
# Right edge shade.
for k in range(4):
    fill_rect(DX1 - 6 - k, DY0 + 40, DX1 - 5 - k, DY1 - 40, (8, 9, 12), 0.35 - k * 0.06)

# Screen: glossy dark glass with a cyan glow readout.
rounded_rect(420, 326, 604, 458, 18, (10, 18, 24), (6, 12, 18))
# Screen glass reflection diagonal.
for k in range(10):
    fill_rect(440 + k * 2, 326, 448 + k * 2, 458, (140, 200, 220), 0.05)
# Screen readout: big infinity-percent, drawn as two rings + "%" glyph,
# centred. No battery bar: it overlapped the text in v1.
draw_infinity(487, 368, 17, (86, 232, 214), w=6)
draw_text(524, 342, "%", (86, 232, 214), scale=9)
sub = "SELF-CHARGING"
tw2 = text_w(sub, 2)
draw_text(512 - tw2 // 2, 428, sub, (120, 190, 200), scale=2)

# USB-C ports: top (cable out) and bottom (cable back in).
rounded_rect_alpha(492, 278, 532, 290, 6, (12, 13, 16), 1.0)
rounded_rect_alpha(492, 794, 532, 806, 6, (12, 13, 16), 1.0)
# Cable connector plugs at both ports.
rounded_rect(496, 264, 528, 290, 6, (88, 92, 100), (52, 55, 62))
rounded_rect(496, 786, 528, 812, 6, (88, 92, 100), (52, 55, 62))
# Power button on the right side.
fill_circle(634, 518, 12, (90, 96, 104), 0.95)
fill_circle(636, 516, 5, (150, 158, 168), 0.9)

# On-device brand label (tiny, product-only text).
brand = "LOOPCELL"
tw3 = text_w(brand, 3)
draw_text(512 - tw3 // 2, 678, brand, (205, 210, 216), scale=3)
model = "MODEL LC-"
tw4 = text_w(model, 2)
mx = draw_text(512 - (tw4 + 26) // 2, 714, model, (140, 146, 154), scale=2)
draw_infinity(mx + 13, 721, 6, (140, 146, 154), w=2)
# Small LED dot, glowing green: it is charging (itself).
fill_circle(512, 754, 6, (60, 220, 130), 0.95)
fill_circle(512, 754, 10, (60, 220, 130), 0.25)
fill_circle(512, 754, 16, (60, 220, 130), 0.10)

# ------------------------------------------------------- accessory: charger --
# Exactly one accessory: the wall charger this gadget never needs. White,
# lying on its side on the floor to the right, prongs up, cable stub coiled.
# Body.
rounded_rect(700, 812, 800, 866, 14, (248, 248, 250), (208, 210, 214))
# Prongs (two metal blades sticking up-left).
fill_rect(712, 792, 718, 814, (190, 194, 200), 1.0)
fill_rect(726, 792, 732, 814, (190, 194, 200), 1.0)
fill_rect(712, 792, 718, 796, (225, 228, 232), 1.0)
fill_rect(726, 792, 732, 796, (225, 228, 232), 1.0)
# Brand dot on the charger.
fill_circle(750, 839, 5, (180, 184, 190), 0.9)
# Short cable stub curling out of the charger, ending in mid-air (unplugged).
stub = cubic((800, 839), (830, 828), (846, 850), (834, 868), 60)
for (x, y) in stub:
    fill_circle(int(x), int(y), 5, (228, 230, 233), 0.95)
for (x, y) in stub:
    fill_circle(int(x) - 2, int(y) - 2, 2, (255, 255, 255), 0.8)
# Tiny shadow under the stub.
for (x, y) in stub[::3]:
    fill_circle(int(x) + 4, int(y) + 8, 4, (90, 94, 100), 0.08)

# ------------------------------------------------------------------- encode --
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


raw = b"".join(b"\x00" + bytes(img[y * W * 3:(y + 1) * W * 3])
               for y in range(H))
png = (b"\x89PNG\r\n\x1a\n" +
       chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) +
       chunk(b"IDAT", zlib.compress(raw, 6)) +
       chunk(b"IEND", b""))

os.makedirs(OUT, exist_ok=True)
with open(PATH, "wb") as f:
    f.write(png)

print(f"Wrote {PATH}: {W}x{H}, {len(png)} bytes")
