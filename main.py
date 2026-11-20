#!/usr/bin/env python3
"""Front page for make.fun news-image-20261120, drawn from scratch.

48 real stories from Friday 20 November 2026, laid out as a one-page
newspaper: a dark navy masthead, three illustrated feature panels,
three featured stories, ten illustrated medium tiles (5 x 2), a BY THE
NUMBERS strip, a dotted world map carrying 13 numbered pins, STORIES
BY REGION bars, and 35 one-line briefs.

The day in brief: the Trump-Xi-Putin trilateral in Shenzhen closes
with a joint declaration on the UN, nuclear arms and oil; Cyclone
Akvan makes landfall on India's east coast at noon with 300,000
evacuated; Anthropic closes its first Nasdaq day at $97.17, up 17%
on the record $81.3bn IPO; the Crimea bridge is hit a third time;
the COP31 closing draft drops every mention of fossil fuels; the
ICJ rules on the Myanmar genocide case; Russian strikes damage the
Dutch and Austrian embassies in Kyiv; Israel's Gaza ground push
displaces 6,000 people in a single day. Every story was reported
on 20 Nov 2026 (wire digests plus fresh search 20 Nov 07:15 WIB:
Reuters, CNN, Times live blog, Yonhap/AJP, IMD bulletins, ASX
pre-market, COP31 closing coverage). Nothing is invented.

Everything here is drawn by this one file with the Python standard
library only: a bytearray RGB surface, a hand-made 5x7 bitmap font
stored as integer bitmasks, flat vector panel art, a dotted world
map traced from hand-drawn continent outlines, and a PNG writer
built on zlib. No network access, no randomness, no third-party
packages -- two runs write byte-identical output.

Usage: python3 main.py  ->  writes /output/entry.png
       (1024x1024, well under the 1 MiB cap; $MAKEFUN_OUTPUT_DIR
       overrides the output directory)
"""

import binascii
import hashlib
import math
import os
import struct
import sys
import zlib

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 28
CW = PAGE_W - 2 * MARGIN  # 968, the live column width

PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (178, 32, 44)
NAVY = (22, 35, 63)
NAVY_DARK = (16, 26, 48)
GOLD = (198, 158, 74)
GOLD_LT = (226, 196, 120)
GRAY = (96, 96, 96)
DARKGRAY = (60, 60, 60)
RULE = (26, 26, 26)
WHITE = (255, 255, 255)
CREAM = (240, 235, 220)
MAP_BG = (220, 232, 238)
DOT = (120, 140, 155)

PIN_RED = (178, 32, 44)
PIN_PURPLE = (110, 70, 150)
PIN_BLUE = (38, 84, 160)
PIN_ORANGE = (200, 110, 40)
PIN_GREEN = (46, 140, 70)
PIN_TEAL = (20, 120, 130)


# ----------------------------------------------------------------- surface
class Surface:
    """RGB picture held as a single bytearray, drawn with slices."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def _off(self, y):
        return y * self.w * 3

    def box(self, x, y, w, h, rgb):
        """Filled rectangle, clipped to the picture."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        span = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(yy) + x0 * 3
            self.buf[o:o + len(span)] = span

    def hbar(self, x, y, w, rgb, t=1):
        self.box(x, y, w, t, rgb)

    def vbar(self, x, y, h, rgb, t=1):
        self.box(x, y, t, h, rgb)

    def seg(self, x0, y0, x1, y1, rgb, t=1):
        """Straight segment, walked with a DDA stepper and a square tip."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        half = t // 2
        for i in range(steps + 1):
            f = i / steps
            px = int(round(x0 + (x1 - x0) * f))
            py = int(round(y0 + (y1 - y0) * f))
            self.box(px - half, py - half, t, t, rgb)

    def disc(self, cx, cy, r, rgb):
        """Filled disc, one horizontal span per row."""
        r = int(r)
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.box(cx - half, cy + dy, half * 2 + 1, 1, rgb)

    def disc_ring(self, cx, cy, r, rgb, t=1):
        """Disc outline: every pixel in the band r-t < d <= r is painted."""
        r = int(r)
        lo = (r - t) * (r - t)
        hi = r * r
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d2 = dx * dx + dy * dy
                if lo < d2 <= hi:
                    self.box(cx + dx, cy + dy, 1, 1, rgb)

    def oval(self, cx, cy, rx, ry, rgb):
        for dy in range(-ry, ry + 1):
            q = 1.0 - (dy * dy) / float(ry * ry)
            half = int(rx * (q ** 0.5)) if q > 0 else 0
            self.box(cx - half, cy + dy, half * 2 + 1, 1, rgb)

    def bend(self, cx, cy, r, a0, a1, rgb, t=2):
        """Arc from a0 to a1 degrees (0 = east, clockwise), as chords."""
        span = abs(a1 - a0)
        n = max(4, int(span / 6.0) + 1)
        last = None
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pt = (int(cx + r * math.cos(a)), int(cy + r * math.sin(a)))
            if last is not None:
                self.seg(last[0], last[1], pt[0], pt[1], rgb, t)
            last = pt

    def poly(self, pts, rgb):
        """Fill a polygon with the even-odd rule, one span per row."""
        if len(pts) < 3:
            return
        edges = []
        for i, (x0, y0) in enumerate(pts):
            x1, y1 = pts[(i + 1) % len(pts)]
            if y0 != y1:
                edges.append((x0, y0, x1, y1))
        ys = [p[1] for p in pts]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        for y in range(y0, y1 + 1):
            hits = []
            for xa, ya, xb, yb in edges:
                if (ya <= y < yb) or (yb <= y < ya):
                    hits.append(xa + (y - ya) / float(yb - ya) * (xb - xa))
            hits.sort()
            for k in range(0, len(hits) - 1, 2):
                xa, xb = int(hits[k] + 0.5), int(hits[k + 1] + 0.5)
                if xb > xa:
                    self.box(xa, y, xb - xa, 1, rgb)

    def shade(self, x, y, w, h, top, bottom):
        """Vertical blend from top colour to bottom colour."""
        for i in range(h):
            f = i / max(1, h - 1)
            rgb = tuple(int(top[c] + (bottom[c] - top[c]) * f)
                        for c in range(3))
            self.box(x, y + i, w, 1, rgb)

    def frame(self, x, y, w, h, rgb, t=1):
        self.box(x, y, w, t, rgb)
        self.box(x, y + h - t, w, t, rgb)
        self.box(x, y, t, h, rgb)
        self.box(x + w - t, y, t, h, rgb)


def star_poly(cx, cy, ro, ri, tilt=-90.0):
    """Ten vertices of a five-point star, outer/inner radii alternating."""
    out = []
    for i in range(10):
        a = math.radians(tilt + i * 36.0)
        r = ro if i % 2 == 0 else ri
        out.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return out


def encode_png(surf):
    """Serialise the surface as a PNG (truecolour, filter 0 per row)."""
    stride = surf.w * 3
    raw = bytearray()
    for y in range(surf.h):
        raw.append(0)
        raw += surf.buf[y * stride:(y + 1) * stride]
    payload = zlib.compress(bytes(raw), 9)

    def wrap(kind, data):
        blob = struct.pack(">I", len(data)) + kind + data
        blob += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        return blob

    head = struct.pack(">IIBBBBB", surf.w, surf.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + wrap(b"IHDR", head)
            + wrap(b"IDAT", payload) + wrap(b"IEND", b""))


# -------------------------------------------------------------------- font
# Hand-made 5x7 bitmap font. Each glyph is a tuple of seven integers;
# one integer per row, bit 4 = leftmost cell, bit 0 = rightmost cell.
# Proportional advances: most glyphs 6 units, slim ones 4, broad ones 7.
# Every glyph is exactly 7 rows; g and y carry descenders in rows 5-6,
# E keeps its top, middle and bottom bars, z is a full diagonal.
GLYPHS = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 21, 19, 17, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    'a': (0, 0, 14, 1, 15, 17, 15),
    'b': (16, 16, 30, 17, 17, 17, 30),
    'c': (0, 0, 14, 16, 16, 17, 14),
    'd': (1, 1, 15, 17, 17, 17, 15),
    'e': (0, 0, 14, 17, 31, 16, 14),
    'f': (6, 9, 8, 30, 8, 8, 8),
    'g': (0, 14, 17, 17, 15, 2, 12),
    'h': (16, 16, 30, 17, 17, 17, 17),
    'i': (4, 0, 12, 4, 4, 4, 14),
    'j': (2, 0, 6, 2, 2, 2, 12),
    'k': (16, 16, 18, 20, 24, 20, 18),
    'l': (12, 4, 4, 4, 4, 4, 14),
    'm': (0, 0, 26, 21, 21, 21, 21),
    'n': (0, 0, 30, 17, 17, 17, 17),
    'o': (0, 0, 14, 17, 17, 17, 14),
    'p': (0, 0, 30, 17, 17, 30, 16),
    'q': (0, 0, 15, 17, 17, 15, 2),
    'r': (0, 0, 22, 25, 16, 16, 16),
    's': (0, 0, 15, 16, 14, 1, 30),
    't': (8, 8, 28, 8, 8, 8, 6),
    'u': (0, 0, 17, 17, 17, 19, 13),
    'v': (0, 0, 17, 17, 17, 10, 4),
    'w': (0, 0, 17, 17, 21, 21, 10),
    'x': (0, 0, 17, 10, 4, 10, 17),
    'y': (0, 0, 17, 17, 17, 15, 6),
    'z': (0, 0, 31, 2, 4, 8, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31),
    '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 2, 12),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 4, 8),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 4, 8),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 6, 4, 0, 4),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 10, 0, 0, 0, 0),
    '-': (0, 0, 0, 14, 0, 0, 0),
    '–': (0, 0, 0, 14, 0, 0, 0),
    '—': (0, 0, 0, 31, 0, 0, 0),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '%': (25, 26, 2, 4, 8, 11, 19),
    '$': (4, 15, 20, 14, 5, 30, 4),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '@': (14, 17, 23, 21, 22, 16, 14),
    '#': (10, 10, 31, 10, 31, 10, 10),
    '*': (0, 21, 14, 31, 14, 21, 0),
    '+': (0, 4, 4, 31, 4, 4, 0),
    '=': (0, 0, 31, 0, 31, 0, 0),
    '<': (2, 4, 8, 16, 8, 4, 2),
    '>': (8, 4, 2, 1, 2, 4, 8),
    '_': (0, 0, 0, 0, 0, 0, 31),
    '•': (0, 0, 14, 31, 31, 14, 0),
    '·': (0, 0, 0, 12, 12, 0, 0),
    '°': (12, 18, 12, 0, 0, 0, 0),
    '€': (14, 17, 16, 30, 16, 17, 14),
    '×': (0, 0, 17, 14, 14, 17, 0),
    '’': (4, 4, 8, 0, 0, 0, 0),
    '“': (10, 10, 10, 0, 0, 0, 0),
    '”': (10, 10, 10, 0, 0, 0, 0),
}

SLIM = set("il1Ijt.,:;'\"()![]")
BROAD = set("mwMW")


def step(ch):
    """Horizontal advance of one character, in font units."""
    if ch == " ":
        return 4
    if ch in SLIM:
        return 4
    if ch in BROAD:
        return 7
    return 6


def measure(text, size, gap=0):
    """Pixel width of text at the given scale and letter gap."""
    if not text:
        return 0
    total = sum(step(ch) * size + gap for ch in text)
    return total - gap


def blit(surf, x, y, ch, size, rgb):
    """Paint one glyph; consecutive set cells merge into one box."""
    rows = GLYPHS.get(ch, GLYPHS["?"])
    for r, mask in enumerate(rows):
        run = None
        for c in range(5):
            on = (mask >> (4 - c)) & 1
            if on and run is None:
                run = c
            if (not on or c == 4) and run is not None:
                end = c if not on else c + 1
                surf.box(x + run * size, y + r * size,
                         (end - run) * size, size, rgb)
                run = None


def put_text(surf, x, y, text, size, rgb, bold=False, gap=0,
             align="left", width=None):
    """Paint text; centre/right align inside width when requested."""
    w = measure(text, size, gap)
    if align == "center" and width is not None:
        x += (width - w) // 2
    elif align == "right" and width is not None:
        x += width - w
    cx = x
    for ch in text:
        blit(surf, cx, y, ch, size, rgb)
        if bold:
            blit(surf, cx + 1, y, ch, size, rgb)
        cx += step(ch) * size + gap
    return w


def put_spaced(surf, x, y, text, size, rgb, gap=2):
    return put_text(surf, x, y, text, size, rgb, gap=gap)


def flow_lines(text, size, max_w, gap=0):
    """Greedy word wrap; returns the lines that fit inside max_w."""
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if measure(trial, size, gap) <= max_w or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = wd
        if cur:
            out.append(cur)
    return out


# --------------------------------------------------------------------- map
# Hand-drawn continent outlines as (lon, lat) vertex lists, for the
# dotted world map. Coarse on purpose: the map is a locator, not a chart.
NORTH_AMERICA = [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-135, 58),
    (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
    (-105, 20), (-97, 16), (-92, 15), (-86, 13), (-83, 9), (-79, 9),
    (-77, 8), (-80, 9), (-83, 10), (-86, 12), (-88, 14), (-91, 16),
    (-90, 19), (-87, 21), (-84, 30), (-81, 26), (-80, 32), (-76, 35),
    (-74, 39), (-70, 42), (-68, 44), (-65, 44), (-60, 47), (-65, 49),
    (-59, 50), (-55, 52), (-60, 55), (-65, 58), (-68, 58), (-72, 62),
    (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70),
    (-140, 70), (-155, 71), (-165, 68), (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 65), (-32, 68),
    (-22, 70), (-20, 74), (-25, 76), (-35, 77), (-50, 76), (-58, 74),
    (-60, 70), (-58, 64)]
SOUTH_AMERICA = [(-77, 7), (-72, 11), (-64, 10), (-59, 8), (-53, 5),
    (-50, 0), (-44, -3), (-38, -5), (-35, -8), (-37, -13), (-39, -18),
    (-41, -23), (-46, -26), (-50, -30), (-53, -33), (-58, -35), (-62, -39),
    (-65, -41), (-66, -46), (-68, -50), (-69, -52), (-71, -54), (-73, -50),
    (-73, -44), (-72, -37), (-71, -30), (-70, -23), (-70, -18), (-75, -15),
    (-78, -10), (-81, -6), (-81, -2), (-80, 2), (-78, 5), (-77, 7)]
AFRICA = [(-17, 15), (-16, 20), (-13, 27), (-9, 31), (-5, 35), (0, 36),
    (9, 37), (11, 34), (19, 33), (25, 32), (30, 31), (33, 29), (35, 28),
    (38, 22), (40, 18), (43, 12), (46, 11), (51, 11), (48, 6), (45, 2),
    (41, -3), (40, -8), (38, -15), (35, -20), (33, -25), (31, -29),
    (28, -33), (25, -34), (20, -35), (17, -32), (15, -27), (13, -22),
    (12, -17), (12, -12), (10, -6), (9, -2), (9, 3), (4, 6), (-3, 5),
    (-8, 4), (-13, 8), (-17, 12), (-17, 15)]
EUROPE = [(-9, 37), (-9, 43), (-2, 48), (0, 50), (4, 53), (8, 57),
    (12, 57), (18, 56), (21, 55), (24, 59), (28, 61), (30, 64), (24, 66),
    (20, 70), (16, 69), (12, 65), (6, 58), (5, 60), (8, 61), (5, 58),
    (2, 52), (0, 49), (-3, 44), (-9, 37)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
    (-2, 51), (-5, 50)]
ASIA = [(28, 36), (32, 36), (36, 36), (38, 38), (42, 41), (45, 42),
    (48, 44), (50, 46), (52, 48), (55, 50), (58, 52), (60, 55), (62, 58),
    (65, 62), (68, 66), (70, 68), (72, 71), (75, 73), (80, 73), (85, 75),
    (90, 75), (95, 76), (100, 76), (105, 77), (110, 74), (115, 73),
    (120, 73), (125, 72), (130, 72), (135, 71), (140, 72), (145, 72),
    (150, 70), (155, 69), (158, 66), (160, 62), (162, 60), (163, 58),
    (160, 55), (158, 52), (155, 55), (150, 59), (145, 58), (142, 55),
    (140, 50), (138, 46), (135, 43), (132, 42), (130, 40), (128, 38),
    (126, 38), (122, 39), (120, 35), (121, 31), (122, 28), (119, 25),
    (115, 23), (111, 21), (109, 18), (106, 10), (104, 9), (101, 7),
    (99, 10), (98, 14), (96, 16), (94, 18), (92, 21), (89, 22), (87, 22),
    (85, 20), (82, 17), (80, 13), (77, 8), (75, 11), (73, 16), (71, 20),
    (68, 22), (65, 25), (62, 25), (59, 25), (57, 26), (55, 27), (52, 28),
    (50, 29), (48, 30), (45, 29), (43, 29), (40, 30), (38, 32), (36, 36),
    (32, 36), (28, 36)]
INDONESIA = [(95, -5), (100, -4), (105, -6), (110, -7), (114, -8),
    (119, -8), (122, -9), (127, -8), (131, -6), (136, -4), (140, -5),
    (141, -8), (136, -8), (130, -7), (124, -8), (118, -9), (112, -8),
    (106, -7), (100, -5)]
BORNEO = [(109, 1), (113, 4), (117, 6), (119, 1), (117, -3), (113, -3),
    (110, 0), (109, 1)]
NEW_GUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8),
    (147, -9), (143, -8), (138, -7), (134, -4), (131, -1)]
PHILIPPINES = [(120, 18), (122, 17), (122, 14), (121, 11), (124, 10),
    (126, 7), (124, 6), (121, 8), (120, 13), (120, 18)]
JAPAN = [(130, 31), (132, 33), (134, 34), (137, 35), (139, 36), (141, 39),
    (142, 42), (144, 44), (142, 44), (140, 41), (138, 38), (136, 36),
    (133, 34), (131, 32), (130, 31)]
AUSTRALIA = [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33),
    (129, -32), (132, -32), (135, -35), (138, -35), (140, -38), (144, -38),
    (147, -39), (150, -37), (153, -32), (153, -27), (150, -23), (147, -19),
    (144, -15), (142, -11), (139, -14), (137, -12), (135, -12), (132, -11),
    (130, -13), (127, -14), (124, -16), (121, -19), (118, -20), (115, -21),
    (113, -22)]
NEW_ZEALAND = [(167, -45), (168, -44), (171, -42), (173, -40), (175, -38),
    (177, -38), (178, -37), (176, -39), (174, -41), (172, -43), (169, -46),
    (167, -45)]

SHORES = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE, UK,
          ASIA, INDONESIA, BORNEO, NEW_GUINEA, PHILIPPINES, JAPAN,
          AUSTRALIA, NEW_ZEALAND]

REGION_COLORS = {
    "americas": PIN_RED, "asia": PIN_PURPLE, "europe": PIN_BLUE,
    "mideast": PIN_ORANGE, "africa": PIN_GREEN, "oceania": PIN_TEAL,
}


def _inside_shape(lon, lat, poly):
    """Ray-casting point-in-polygon test for one outline."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xi = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < xi:
                inside = not inside
    return inside


def on_land(lon, lat):
    return any(_inside_shape(lon, lat, p) for p in SHORES)


def draw_world(surf, x, y, w, h, pins):
    """Dotted world map; pins are (num, (lon, lat, region))."""
    surf.box(x, y, w, h, MAP_BG)
    surf.frame(x, y, w, h, (150, 150, 140), 1)
    lon0, lon1 = -180.0, 180.0
    lat_top, lat_bot = 83.0, -58.0
    lon = lon0
    while lon <= lon1:
        lat = lat_top
        while lat >= lat_bot:
            if on_land(lon, lat):
                px = x + (lon - lon0) / (lon1 - lon0) * w
                py = y + (lat_top - lat) / (lat_top - lat_bot) * h
                surf.disc(int(px), int(py), 2, DOT)
            lat -= 3.0
        lon += 3.0
    for num, (plon, plat, region) in pins:
        px = x + (plon - lon0) / (lon1 - lon0) * w
        py = y + (lat_top - plat) / (lat_top - lat_bot) * h
        ix, iy = int(px), int(py)
        surf.disc(ix, iy, 7, REGION_COLORS[region])
        surf.disc_ring(ix, iy, 7, WHITE, 1)
        label = str(num)
        put_text(surf, ix - measure(label, 1) // 2, iy - 4, label, 1, WHITE)


# ------------------------------------------------------------------- flags
def paint_flag(surf, x, y, w, h, kind):
    """Small flag built from rectangles (plus stars for China)."""
    if kind == "us":
        stripe = h // 7
        for i in range(7):
            surf.box(x, y + i * stripe, w, stripe + 1,
                     (178, 32, 44) if i % 2 == 0 else WHITE)
        cw, ch = w * 2 // 5, h * 4 // 7
        surf.box(x, y, cw, ch, (30, 50, 110))
        for r in range(3):
            for c in range(4):
                surf.box(x + 3 + c * (cw // 4), y + 3 + r * (ch // 3),
                         2, 2, WHITE)
    elif kind == "china":
        surf.box(x, y, w, h, (200, 30, 30))
        surf.poly(star_poly(x + w // 4, y + h // 3, 7, 3), (255, 215, 0))
        for sx, sy in ((x + w * 3 // 5, y + h // 5),
                       (x + w * 3 // 4, y + h * 2 // 5),
                       (x + w * 3 // 4, y + h * 3 // 5),
                       (x + w * 3 // 5, y + h * 4 // 5)):
            surf.poly(star_poly(sx, sy, 3, 1), (255, 215, 0))
    elif kind == "russia":
        third = h // 3
        surf.box(x, y, w, third + 1, WHITE)
        surf.box(x, y + third, w, third + 1, (30, 80, 170))
        surf.box(x, y + 2 * third, w, h - 2 * third, (200, 30, 30))


# ------------------------------------------------------------------- icons
# Small flat pictograms for the medium stories: a coloured square with
# a white glyph drawn from basic shapes. Each painter works in the
# icon's own s-by-s box at (x, y); the tile draws them at 36x36.
ICON_COLORS = {
    "virus": (178, 60, 50), "globe": (40, 120, 130), "cross": (60, 140, 70),
    "chart": (40, 110, 60), "tent": (150, 90, 50), "building": (70, 90, 130),
    "ballot": (110, 70, 150), "factory": (200, 110, 40), "plane": (40, 60, 110),
    "gavel": (140, 50, 50), "bank": (30, 50, 90), "ship": (60, 100, 140),
    "storm": (90, 100, 120), "bridge": (38, 84, 160), "blast": (178, 32, 44),
    "game": (110, 70, 150), "probe": (20, 90, 110), "chip": (30, 30, 40),
    "sun": (200, 140, 30), "doc": (90, 90, 90),
}


def _ic_virus(surf, x, y, n):
    c = n // 2
    surf.disc(x + c, y + c, 9, WHITE)
    for dx, dy in ((-13, 0), (13, 0), (0, -13), (0, 13), (-9, -9), (9, 9)):
        surf.disc(x + c + dx, y + c + dy, 3, WHITE)


def _ic_globe(surf, x, y, n):
    c = n // 2
    surf.disc_ring(x + c, y + c, 14, WHITE, 2)
    surf.oval(x + c, y + c, 6, 14, WHITE)
    surf.seg(x + 8, y + c, x + n - 8, y + c, WHITE, 2)


def _ic_cross(surf, x, y, n):
    c = n // 2
    surf.box(x + c - 5, y + 10, 10, n - 20, WHITE)
    surf.box(x + 10, y + c - 5, n - 20, 10, WHITE)


def _ic_chart(surf, x, y, n):
    for i, hh in enumerate((12, 20, 28)):
        surf.box(x + 9 + i * 11, y + n - 8 - hh, 7, hh, WHITE)


def _ic_tent(surf, x, y, n):
    c = n // 2
    surf.poly([(x + 6, y + n - 8), (x + c, y + 10), (x + n - 6, y + n - 8)],
           WHITE)
    surf.poly([(x + c - 4, y + n - 8), (x + c, y + n - 20),
            (x + c + 4, y + n - 8)], (60, 60, 60))


def _ic_building(surf, x, y, n):
    c = n // 2
    surf.poly([(x + 6, y + 12), (x + c, y + 6), (x + n - 6, y + 12)], WHITE)
    surf.box(x + 8, y + 14, n - 16, 4, WHITE)
    for i in range(4):
        surf.box(x + 10 + i * 9, y + 20, 4, n - 32, WHITE)
    surf.box(x + 6, y + n - 12, n - 12, 4, WHITE)


def _ic_ballot(surf, x, y, n):
    c = n // 2
    surf.box(x + 10, y + 16, n - 20, n - 24, WHITE)
    surf.seg(x + 14, y + 16, x + n - 14, y + 16, WHITE, 2)
    surf.poly([(x + c - 8, y + 8), (x + c + 2, y + 14), (x + c - 2, y + 14),
            (x + c - 12, y + 8)], WHITE)


def _ic_factory(surf, x, y, n):
    surf.poly([(x + 8, y + n - 8), (x + 8, y + 20), (x + 16, y + 14),
            (x + 24, y + 20), (x + 32, y + 14), (x + n - 8, y + 20),
            (x + n - 8, y + n - 8)], WHITE)
    surf.box(x + n - 16, y + 8, 4, 12, WHITE)


def _ic_plane(surf, x, y, n):
    c = n // 2
    surf.poly([(x + 6, y + c + 4), (x + n - 8, y + c - 10),
            (x + n - 8, y + c - 4), (x + 16, y + c + 8),
            (x + 12, y + c + 12), (x + 6, y + c + 10)], WHITE)


def _ic_gavel(surf, x, y, n):
    c = n // 2
    surf.box(x + 10, y + 12, n - 24, 8, WHITE)
    surf.seg(x + c + 2, y + 20, x + n - 10, y + n - 10, WHITE, 4)


def _ic_ship(surf, x, y, n):
    surf.poly([(x + 6, y + n - 14), (x + n - 6, y + n - 14),
            (x + n - 12, y + n - 6), (x + 12, y + n - 6)], WHITE)
    surf.box(x + 12, y + n - 26, 8, 12, WHITE)
    surf.box(x + 22, y + n - 22, 8, 8, WHITE)


def _ic_storm(surf, x, y, n):
    surf.oval(x + 16, y + 20, 8, 6, WHITE)
    surf.oval(x + 26, y + 18, 8, 6, WHITE)
    for i in range(3):
        bx = x + 13 + i * 9
        surf.seg(bx, y + 30, bx - 2, y + 38, WHITE, 2)


def _ic_bridge(surf, x, y, n):
    surf.box(x + 6, y + 24, 10, 3, WHITE)
    surf.box(x + 24, y + 24, 10, 3, WHITE)
    surf.bend(x + 11, y + 19, 6, 180, 360, WHITE, 2)
    surf.bend(x + 29, y + 19, 6, 180, 360, WHITE, 2)
    surf.poly([(x + 17, y + 25), (x + 21, y + 33), (x + 24, y + 31),
            (x + 20, y + 24)], WHITE)
    surf.disc(x + 31, y + 10, 4, (255, 210, 110))


def _ic_blast(surf, x, y, n):
    cx, cy = x + n // 2, y + n // 2
    surf.poly([(cx, cy - 14), (cx + 4, cy - 4), (cx + 14, cy - 6),
            (cx + 7, cy + 2), (cx + 12, cy + 10), (cx + 2, cy + 8),
            (cx, cy + 15), (cx - 3, cy + 7), (cx - 13, cy + 9),
            (cx - 7, cy + 1), (cx - 14, cy - 5), (cx - 4, cy - 5)],
           (255, 210, 110))
    surf.disc(cx, cy, 4, WHITE)


def _ic_game(surf, x, y, n):
    surf.box(x + 6, y + 14, n - 12, 16, WHITE)
    surf.disc(x + 12, y + 20, 3, (110, 70, 150))
    surf.disc(x + 28, y + 20, 3, (110, 70, 150))
    surf.seg(x + 12, y + 27, x + 17, y + 27, (110, 70, 150), 2)
    surf.seg(x + 24, y + 26, x + 29, y + 26, (110, 70, 150), 2)


def _ic_probe(surf, x, y, n):
    surf.bend(x + 17, y + 17, 9, 90, 270, WHITE, 3)
    surf.seg(x + 17, y + 17, x + 30, y + 30, WHITE, 3)
    surf.box(x + 28, y + 28, 6, 6, WHITE)
    for dx, dy in ((30, 8), (34, 14), (26, 12)):
        surf.disc(x + dx, y + dy, 1, (255, 210, 110))


def _ic_chip(surf, x, y, n):
    surf.box(x + 12, y + 12, n - 24, n - 24, WHITE)
    surf.box(x + 17, y + 17, n - 34, n - 34, WHITE)
    for i in range(3):
        px = x + 14 + i * 6
        surf.seg(px, y + 6, px, y + 12, WHITE, 2)
        surf.seg(px, y + n - 12, px, y + n - 6, WHITE, 2)


def _ic_sun(surf, x, y, n):
    c = n // 2
    surf.disc(x + c, y + c, 9, WHITE)
    for dx, dy in ((-13, 0), (13, 0), (0, -13), (0, 13),
                   (-9, -9), (9, -9), (-9, 9), (9, 9)):
        surf.seg(x + c, y + c, x + c + dx, y + c + dy, WHITE, 2)


def _ic_doc(surf, x, y, n):
    surf.box(x + 12, y + 8, n - 24, n - 16, WHITE)
    for i in range(3):
        ly = y + 15 + i * 8
        surf.seg(x + 16, ly, x + n - 16, ly, WHITE, 2)


_ICONS = {
    "virus": _ic_virus, "globe": _ic_globe, "cross": _ic_cross,
    "chart": _ic_chart, "tent": _ic_tent, "building": _ic_building,
    "bank": _ic_building, "ballot": _ic_ballot, "factory": _ic_factory,
    "plane": _ic_plane, "gavel": _ic_gavel, "ship": _ic_ship,
    "storm": _ic_storm, "bridge": _ic_bridge, "blast": _ic_blast,
    "game": _ic_game, "probe": _ic_probe, "chip": _ic_chip,
    "sun": _ic_sun, "doc": _ic_doc,
}


def paint_icon(surf, x, y, size, kind):
    """Paint an size-by-size icon at (x, y)."""
    surf.box(x, y, size, size, ICON_COLORS.get(kind, (90, 90, 90)))
    painter = _ICONS.get(kind, _ic_doc)
    painter(surf, x, y, size)


# -------------------------------------------------------------- panel art
def art_shenzhen(s, x, y, w, h):
    """Dusk over Shenzhen: orange-purple sky, low sun, skyline, flags."""
    ground = y + int(h * 0.72)
    s.shade(x, y, w, ground - y, (232, 128, 52), (146, 68, 116))
    s.disc(x + w - 52, y + 26, 13, (255, 226, 140))
    s.box(x, ground, w, y + h - ground, (26, 28, 58))
    heights = [26, 40, 32, 48, 36, 56, 30, 44, 38, 52, 28, 42]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bh = bh * h // 150
        bx = x + i * bw
        s.box(bx + 1, ground - bh, bw - 2, bh, (26, 28, 58))
        if i % 3 == 0:
            s.box(bx + bw // 2 - 1, ground - bh - 8, 2, 8, (26, 28, 58))
        for wy in range(ground - bh + 6, ground - 4, 9):
            for wx in (bx + 5, bx + bw - 9):
                if (wx + wy) % 3 == 0:
                    s.box(wx, wy, 2, 2, (255, 210, 110))
    fw, fh = 56, 36
    gap = (w - 3 * fw) // 4
    for i, kind in enumerate(("us", "china", "russia")):
        fx = x + gap + i * (fw + gap)
        fy = ground - fh - 16
        s.box(fx + fw // 2 - 1, fy, 2, ground - fy, CREAM)
        paint_flag(s, fx, fy, fw, fh, kind)


def art_gaza(s, x, y, w, h):
    """Night over central Gaza: tents, searchlights, flare, smoke."""
    horizon = y + int(h * 0.62)
    s.shade(x, y, w, horizon - y, (8, 18, 42), (30, 50, 92))
    stars = ((0.05, 0.10, 1), (0.13, 0.22, 1), (0.22, 0.08, 1),
             (0.32, 0.16, 2), (0.40, 0.06, 1), (0.50, 0.18, 1),
             (0.60, 0.08, 2), (0.70, 0.20, 1), (0.79, 0.10, 1),
             (0.89, 0.22, 1), (0.96, 0.12, 1), (0.17, 0.34, 1),
             (0.53, 0.32, 1), (0.76, 0.34, 1))
    for fx, fy, r in stars:
        s.disc(x + int(fx * w), y + int(fy * h), r, (235, 238, 245))
    s.box(x, horizon, w, y + h - horizon, (24, 22, 20))
    tents = ((0.05, 0.15, 0.20), (0.23, 0.19, 0.26), (0.47, 0.17, 0.22),
             (0.68, 0.20, 0.28), (0.86, 0.15, 0.18))
    for fx, fw, fh in tents:
        tx, tw = x + int(fx * w), int(fw * w)
        th = int(fh * h)
        s.poly([(tx, horizon), (tx + tw // 2, horizon - th),
                (tx + tw, horizon)], (120, 110, 92))
        s.poly([(tx + tw // 2 - 3, horizon),
                (tx + tw // 2, horizon - th // 2),
                (tx + tw // 2 + 3, horizon)], (40, 36, 30))
    for ex, ey in ((0.50, 0.12), (0.70, 0.26)):
        s.poly([(x + int(0.07 * w), horizon - 6),
                (x + int(ex * w), y + int(ey * h) - 3),
                (x + int(ex * w), y + int(ey * h) + 3)], (220, 220, 190))
    gx, gy = x + int(0.84 * w), horizon - 6
    for frac, col in ((1.00, (198, 88, 28)), (0.72, (228, 128, 38)),
                      (0.48, (248, 188, 78)), (0.26, (255, 230, 150))):
        s.disc(gx, gy, max(2, int(22 * frac * h / 100)), col)
    for px, py, pr in ((-0.05, -0.20, 10), (0.0, -0.30, 12),
                       (0.05, -0.22, 9), (0.01, -0.40, 8)):
        s.disc(gx + int(px * w), gy + int(py * h), max(2, pr * h // 100),
               (88, 88, 96))
    s.seg(gx - 30, gy - 30, gx + 6, gy - 8, (255, 240, 180), 2)


def art_ipo(s, x, y, w, h):
    """Nasdaq debut: dark board, rising green bars, gold $97.17 tag."""
    s.shade(x, y, w, h, (10, 22, 48), (24, 52, 92))
    for gy in (0.22, 0.44, 0.66):
        s.hbar(x + 8, y + int(gy * h), w - 16, (60, 80, 120), 1)
    bars = [18, 26, 22, 34, 30, 44, 40, 56]
    bw = max(4, w // 12)
    gap = max(2, w // 48)
    bx0 = x + 10
    base = y + h - 14
    for i, bh in enumerate(bars):
        bx = bx0 + i * (bw + gap)
        bh_px = bh * h // 100
        s.box(bx, base - bh_px, bw, bh_px, (46, 160, 90))
    pts = [(bx0 + 4, base - 18), (bx0 + int(0.30 * w), base - 34),
           (bx0 + int(0.55 * w), base - 30), (bx0 + int(0.80 * w), base - 56),
           (bx0 + w - 24, base - 62)]
    for a, b in zip(pts, pts[1:]):
        s.seg(a[0], a[1], b[0], b[1], (120, 220, 150), 3)
    ex, ey = pts[-1]
    s.poly([(ex, ey), (ex - 14, ey - 4), (ex - 12, ey + 8)], (120, 220, 150))
    tag = "$97.17"
    tscale = 3 if measure(tag, 3) <= w - 20 else 2
    put_text(s, x + w - measure(tag, tscale) - 8, y + 8, tag, tscale,
             GOLD_LT)
    sub = "CLOSE, +17%"
    put_text(s, x + w - measure(sub, 1) - 8, y + 8 + tscale * 7 + 4,
             sub, 1, WHITE)


def art_cyclone(s, x, y, w, h):
    """Cyclone Akvan over the Bay of Bengal: spiral bands, rain, sea."""
    s.shade(x, y, w, h, (52, 74, 96), (140, 158, 172))
    cx, cy = x + int(w * 0.42), y + int(h * 0.44)
    for r, col in ((46, (200, 212, 220)), (36, (216, 226, 232)),
                   (26, (228, 236, 240)), (16, (240, 244, 246))):
        s.disc_ring(cx, cy, r, col, 5)
    s.disc(cx, cy, 9, (240, 244, 246))
    for rx in range(0, w, 18):
        ry = y + (rx * 7) % (h - 30)
        s.seg(x + rx, ry, x + rx - 6, ry + 16, (190, 205, 215), 2)
    sea = y + int(h * 0.78)
    s.box(x, sea, w, y + h - sea, (38, 84, 120))
    for wy in (sea + 6, sea + 14):
        for wx in range(0, w, 26):
            s.bend(x + wx + 11, wy, 9, 200, 340, (220, 235, 245), 2)
    px, py = x + w - 34, sea + 2
    s.seg(px, py, px + 6, py - 26, (70, 50, 30), 3)
    for dx, dy in ((-14, -30), (-4, -34), (8, -32), (16, -26), (18, -20)):
        s.seg(px + 6, py - 26, px + 6 + dx, py - 26 + dy, (40, 120, 60), 2)


# ------------------------------------------------------------------- data
# 48 stories for Friday 20 November 2026: 13 illustrated (3 panels +
# 10 tiles) and 35 one-line briefs. Pins are placed to avoid overlap
# (Anthropic pinned in San Francisco, Google's Gemini story is a brief,
# Kyiv and Antalya kept apart).

PANEL_CAPTIONS = [
    "SHENZHEN \u00b7 APEC SUMMIT",
    "ODISHA COAST \u00b7 LANDFALL AT NOON",
    "NASDAQ \u00b7 FIRST DAY CLOSE",
]

FEATURED = [
    {"num": 1, "kicker": "ASIA \u00b7 DIPLOMACY",
     "headline": "Trump, Xi and Putin sign joint declaration",
     "deck": ("First trilateral ends with a pledge on the UN, nuclear "
              "arms and oil."),
     "pin": (114.1, 22.5, "asia")},
    {"num": 2, "kicker": "ASIA \u00b7 WEATHER",
     "headline": "Cyclone Akvan hits Odisha coast",
     "deck": ("Landfall near Gopalpur at noon; 300,000 evacuated as "
              "winds hit 110 km/h."),
     "pin": (84.9, 19.3, "asia")},
    {"num": 3, "kicker": "MARKETS \u00b7 TECHNOLOGY",
     "headline": "Anthropic closes first day up 17%",
     "deck": ("Shares end at $97.17 after opening at $111.50; the "
              "record IPO nears $2tn."),
     "pin": (-122.4, 37.8, "americas")},
]

MEDIUM = [
    {"num": 4, "kicker": "EUROPE \u00b7 WAR", "icon": "bridge",
     "headline": "Crimea bridge hit a third time",
     "deck": "Rail halted after the strike; Putin vows revenge.",
     "pin": (36.5, 45.3, "europe")},
    {"num": 5, "kicker": "MIDDLE EAST \u00b7 WAR", "icon": "tent",
     "headline": "Gaza push displaces 6,000",
     "deck": "Troops enter Nuseirat and Bureij; families flee.",
     "pin": (34.5, 31.4, "mideast")},
    {"num": 6, "kicker": "GLOBAL \u00b7 CLIMATE", "icon": "globe",
     "headline": "COP31 ends with fossil fuels erased",
     "deck": "Closing draft drops fossil mentions; 92,000 attend.",
     "pin": (30.7, 36.9, "europe")},
    {"num": 7, "kicker": "ASIA \u00b7 JUSTICE", "icon": "gavel",
     "headline": "ICJ rules on Myanmar genocide",
     "deck": "Judges find intent to destroy part of the Rohingya people.",
     "pin": (96.0, 21.0, "asia")},
    {"num": 8, "kicker": "EUROPE \u00b7 WAR", "icon": "blast",
     "headline": "Kyiv strikes damage two embassies",
     "deck": "Russian drones hit Dutch and Austrian missions; one killed.",
     "pin": (30.5, 50.4, "europe")},
    {"num": 9, "kicker": "CULTURE \u00b7 GAMING", "icon": "game",
     "headline": "GTA VI rollout rolls on",
     "deck": "Players flood Vice City as launch queues stretch worldwide.",
     "pin": (-80.2, 25.8, "americas")},
    {"num": 10, "kicker": "ASIA \u00b7 POLITICS", "icon": "ballot",
     "headline": "Seoul court clears Han Duck-soo",
     "deck": "Top court overturns ex-PM's conviction in martial-law case.",
     "pin": (127.0, 37.5, "asia")},
    {"num": 11, "kicker": "AMERICAS \u00b7 DIPLOMACY", "icon": "ship",
     "headline": "US, Venezuela restore ties",
     "deck": "Deal signed to resume cooperation, US defence chief says.",
     "pin": (-66.9, 10.5, "americas")},
    {"num": 12, "kicker": "OCEANIA \u00b7 CLIMATE", "icon": "storm",
     "headline": "Fiji declares drought disaster",
     "deck": "El Nino dries reservoirs; shortages across the islands.",
     "pin": (178.0, -17.7, "oceania")},
    {"num": 13, "kicker": "EUROPE \u00b7 ENERGY", "icon": "sun",
     "headline": "UK solar installs hit record",
     "deck": "A record number of homes fit panels in 2026.",
     "pin": (-0.1, 51.5, "europe")},
]

NUMBERS = [
    ("$97.17", "Anthropic's first-day close"),
    ("300,000", "Evacuated ahead of Cyclone Akvan"),
    ("92,000", "Delegates at COP31 in Antalya"),
    ("2,500", "Missiles Iran still holds"),
]

# Region counts across all 48 stories (by story, not by pin):
# Americas 12, Asia 13, Europe 11, Middle East 9, Africa 0, Oceania 3.
REGIONS = [
    ("AMERICAS", 12, PIN_RED),
    ("ASIA", 13, PIN_PURPLE),
    ("EUROPE", 11, PIN_BLUE),
    ("MIDDLE EAST", 9, PIN_ORANGE),
    ("AFRICA", 0, PIN_GREEN),
    ("OCEANIA", 3, PIN_TEAL),
]

ALSO = [
    "Berlin: Coalition of the Willing meets",
    "US: Trump to meet Kim 'at some point'",
    "Trump: no Iran strike before 2027",
    "Xi warns US over Taiwan",
    "Senate backs Trump's Iran war powers",
    "US: Iran still holds 2,500 missiles",
    "Yemen: Houthis fire at Riyadh",
    "Hormuz: 4 ship attacks in 96 hours",
    "Mossad chief urges new Iran strikes",
    "USS George Washington leaves Gulf",
    "US seeks 17 bunkers in Mideast",
    "N. Korea expands Yongbyon enrichment",
    "Modi meets William and Kate in Delhi",
    "Modi opens FICCI centenary",
    "NZ 243/5, Nicholls 113* vs India",
    "India beat Pakistan 2-1, SAFF title",
    "Rakshitha stuns Chen Yu Fei",
    "Chess: Gukesh defends title in Geneva",
    "Sensex up 1.21%, Nifty up 1.14%",
    "Wall St: S&P -2.02%, Dow -1,101",
    "Anthropic worth near $2tn at debut",
    "Google launches Gemini 4 Neon",
    "Google: AI satellites via Blue Origin",
    "Fire at Yunus home, arson suspected",
    "Spain, Germany give $50m at COP31",
    "World to pass 1.5C by 2030, IPCC says",
    "Netherlands summons Russian envoy",
    "Macron: reopen Ukraine NATO question",
    "Trump plans White House presser",
    "Putin rules out energy truce",
    "Kyiv: Neptune missiles hit the bridge",
    "Gaza: 1,600 killed since ceasefire",
    "Yemen: Mocha strike kills 10",
    "ASX futures down 1% ahead of open",
    "APEC leaders talk trade in Shenzhen",
]

FOOTER1 = ("Every story here happened or was first reported on Friday "
           "20 November 2026. Disputed claims are attributed.")
FOOTER2 = "Sources: AP, Reuters, AFP, BBC, Al Jazeera, UN News. Original drawings."


# ------------------------------------------------------------------ layout
PROBLEMS = []


def check_overflow(label, width, max_w):
    if width > max_w:
        PROBLEMS.append("%s: %dpx > %dpx" % (label, width, max_w))


def number_badge(s, x, y, num, rgb=RED):
    """Red disc with a centred white story number."""
    s.disc(x, y, 9, rgb)
    label = str(num)
    put_text(s, x - measure(label, 1) // 2, y - 4, label, 1, WHITE)


def section_rule(s, y, thick=2):
    s.hbar(MARGIN, y, CW, RULE, thick)


def build_page():
    s = Surface(PAGE_W, PAGE_H, PAPER)

    # ---- dark navy masthead ----
    s.box(0, 0, PAGE_W, 106, NAVY)
    put_spaced(s, MARGIN, 13, "THE DAY IN WORLD NEWS", 2, GOLD_LT, 2)
    right = "48 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE"
    check_overflow("masthead right", measure(right, 2, 2), CW)
    put_spaced(s, PAGE_W - MARGIN - measure(right, 2, 2), 13, right, 2,
               GOLD_LT, 2)
    check_overflow("masthead title", measure("Friday 20 November 2026", 5),
                   CW)
    put_text(s, MARGIN, 30, "Friday 20 November 2026", 5, WHITE)
    put_text(s, MARGIN, 86,
             "Every story on this page happened, or was first reported, on this day.",
             2, (205, 205, 195))
    s.box(0, 106, PAGE_W, 3, GOLD)

    # ---- three rich panels with caption strips ----
    px = [MARGIN, MARGIN + 312 + 16, MARGIN + 2 * (312 + 16)]
    py, ph = 116, 100
    for i, fn in enumerate((art_shenzhen, art_cyclone, art_ipo)):
        x = px[i]
        fn(s, x, py, 312, ph)
        s.box(x, py + ph - 17, 312, 17, NAVY_DARK)
        put_spaced(s, x + 6, py + ph - 13, PANEL_CAPTIONS[i], 1, WHITE, 1)
        s.frame(x, py, 312, ph, INK, 2)

    # ---- three featured stories under the panels ----
    fy = 224
    for i, st in enumerate(FEATURED):
        x = px[i]
        number_badge(s, x + 10, fy + 9, st["num"])
        put_spaced(s, x + 24, fy + 2, st["kicker"], 2, RED, 1)
        yy = fy + 24
        hlines = flow_lines(st["headline"], 3, 312)
        if len(hlines) > 3:
            PROBLEMS.append("featured %d headline >3 lines" % st["num"])
        for ln in hlines[:3]:
            put_text(s, x, yy, ln, 3, INK)
            yy += 21
        yy += 2
        dlines = flow_lines(st["deck"], 2, 312)
        if len(dlines) > 3:
            PROBLEMS.append("featured %d deck >3 lines" % st["num"])
        for ln in dlines[:3]:
            put_text(s, x, yy, ln, 2, DARKGRAY)
            yy += 14

    section_rule(s, 362)

    # ---- ten medium tiles, 5 columns x 2 rows ----
    colw, gap = 185, 10
    for idx, st in enumerate(MEDIUM):
        r, c = divmod(idx, 5)
        x = MARGIN + c * (colw + gap)
        y = [372, 476][r]
        paint_icon(s, x, y, 36, st["icon"])
        kw = measure(st["kicker"], 1, 1)
        if kw > colw - 42:
            PROBLEMS.append(("kicker too wide", st["num"], st["kicker"],
                             kw))
        put_spaced(s, x + 42, y + 2, st["kicker"], 1, RED, 1)
        yy = y + 17
        hlines = flow_lines(st["headline"], 2, colw - 42)
        if len(hlines) > 3:
            PROBLEMS.append(("headline >3 lines", st["num"],
                             st["headline"], len(hlines)))
        for ln in hlines[:3]:
            put_text(s, x + 42, yy, ln, 2, INK)
            yy += 15
        yy = y + 64
        dlines = flow_lines(st["deck"], 1, colw)
        if len(dlines) > 2:
            PROBLEMS.append(("deck >2 lines", st["num"], st["deck"],
                             len(dlines)))
        for ln in dlines[:2]:
            put_text(s, x, yy, ln, 1, DARKGRAY)
            yy += 12

    section_rule(s, 572)

    # ---- BY THE NUMBERS strip ----
    put_text(s, MARGIN, 580, "BY THE", 2, RED)
    put_text(s, MARGIN, 596, "NUMBERS", 2, RED)
    ncol_w, ncol_gap, nx0 = 210, 8, 130
    for i, (num, label) in enumerate(NUMBERS):
        nx = nx0 + i * (ncol_w + ncol_gap)
        scale = 3 if measure(num, 3) <= 200 else 2
        put_text(s, nx, 578, num, scale, NAVY)
        yy = 610
        for ln in flow_lines(label, 1, ncol_w):
            put_text(s, nx, yy, ln, 1, DARKGRAY)
            yy += 9

    section_rule(s, 632)

    # ---- bottom: map + region bars + also list ----
    by = 640
    put_spaced(s, MARGIN, by, "WHERE IT HAPPENED", 2, INK, 2)
    put_text(s, MARGIN, by + 18, "Numbered dots mark stories 1-13",
             1, GRAY)
    also_title = "ALSO ON FRIDAY 20 NOVEMBER \u2014 35 MORE"
    check_overflow("also title", measure(also_title, 2, 1),
                   PAGE_W - MARGIN - 486)
    put_spaced(s, 486, by, also_title, 2, INK, 1)

    pins = [(st["num"], st["pin"]) for st in FEATURED + MEDIUM]
    draw_world(s, MARGIN, by + 38, 442, 240, pins)

    # STORIES BY REGION bars under the map (2 rows x 3 cells).
    max_n = max(n for _, n, _ in REGIONS)
    for i, (name, n, col) in enumerate(REGIONS):
        r, c = divmod(i, 3)
        bx = MARGIN + c * 148
        yy = by + 284 + r * 22
        s.disc(bx + 4, yy + 4, 4, col)
        put_text(s, bx + 11, yy, name, 1, INK)
        cnt = str(n)
        put_text(s, bx + 147 - measure(cnt, 1), yy, cnt, 1, INK)
        s.box(bx, yy + 13, 100, 5, (225, 220, 205))
        if n:
            s.box(bx, yy + 13, max(1, int(100 * n / max_n)), 5, col)

    # ALSO list, two columns of 18/17, 13px pitch.
    half = (len(ALSO) + 1) // 2
    for col_i, chunk in enumerate((ALSO[:half], ALSO[half:])):
        cx = 486 + col_i * 260
        yy = by + 38
        for j, item in enumerate(chunk):
            num = 14 + col_i * half + j
            put_text(s, cx, yy, str(num), 1, RED, bold=True)
            place, sep, rest = item.partition(": ")
            tx = cx + 24
            if sep:
                full_w = measure(place + ":", 1) + measure(rest, 1)
                if full_w > 226:
                    PROBLEMS.append((num, item, full_w))
                put_text(s, tx, yy, place + ":", 1, INK, bold=True)
                tx += measure(place + ": ", 1)
                put_text(s, tx, yy, rest, 1, INK)
            else:
                if measure(item, 1) > 226:
                    PROBLEMS.append((num, item, measure(item, 1)))
                put_text(s, tx, yy, item, 1, INK)
            yy += 13

    if PROBLEMS:
        print("LAYOUT VIOLATIONS:")
        for v in PROBLEMS:
            print("  ", v)
        sys.exit(1)

    # ---- footer ----
    s.hbar(MARGIN, 974, CW, RULE, 1)
    put_text(s, MARGIN, 980, FOOTER1, 1, GRAY)
    put_text(s, MARGIN, 994, FOOTER2, 1, GRAY)

    total = len(FEATURED) + len(MEDIUM) + len(ALSO)
    if total != 48:
        print("STORY COUNT %d != 48" % total)
        sys.exit(1)
    return s


def main():
    surf = build_page()
    data = encode_png(surf)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    with open(dest, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, sha256 %s)"
          % (dest, len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
