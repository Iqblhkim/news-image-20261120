#!/usr/bin/env python3
"""Draw the front page for make.fun news-image-20261120.

48 stories for Friday 20 November 2026, in the winning one-page
newspaper style (cf. the winning entries of the 17-19 Nov editions:
36-43 stories, first 13 illustrated, a map, a numbers strip): dark
navy masthead, three rich illustrated panels, three featured stories,
TEN illustrated medium tiles (5 columns x 2 rows), a BY THE NUMBERS
strip, a dotted world map with numbered pins, STORIES BY REGION bars,
and an ALSO list of 35 one-line briefs. 13 stories illustrated in
total (3 panels + 10 tiles).

The day: the Trump-Xi-Putin trilateral in Shenzhen ends with a joint
declaration on the UN, nuclear arms and oil; Cyclone Akvan makes
landfall on India's east coast at noon, 300,000 evacuated; Anthropic
closes its first Nasdaq day at $97.17, up 17% on the record $81.3bn
IPO; the Crimea bridge is hit a third time; the COP31 closing draft
drops every mention of fossil fuels; the ICJ rules on the Myanmar
genocide case; Russian strikes damage the Dutch and Austrian
embassies in Kyiv; Israel's Gaza ground push displaces 6,000 people
in a day. Nothing invented: every story was reported on 20 Nov 2026
(wire digests + fresh search 20 Nov 07:15 WIB: Reuters, CNN, Times
live blog, Yonhap/AJP, IMD bulletins, ASX pre-market, COP31 closing
coverage).

This program draws the whole page itself with the Python standard
library only: a small RGB canvas, a hand-made 5x7 bitmap font, flat
vector panel art, a dotted world map from hand-drawn continent
outlines, and a PNG encoder built on zlib. No network, no randomness,
no third-party packages -- running it twice writes the same bytes.
It writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Usage: python3 main.py  ->  writes /output/entry.png (1024x1024, <=1 MiB)
"""

import binascii
import hashlib
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024
MARGIN = 28
CW = W - 2 * MARGIN  # 968

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


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB canvas backed by one bytearray; all drawing is slice work."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _row(self, y):
        return y * self.w * 3

    def rect(self, x, y, w, h, col):
        """Filled rectangle, clipped to the canvas."""
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        span = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._row(yy) + x0 * 3
            self.px[o:o + len(span)] = span

    def hline(self, x, y, w, col, thick=1):
        self.rect(x, y, w, thick, col)

    def vline(self, x, y, h, col, thick=1):
        self.rect(x, y, thick, h, col)

    def line(self, x0, y0, x1, y1, col, thick=1):
        """Bresenham line with a square brush."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.rect(x0 - half, y0 - half, thick, thick, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, col):
        """Filled circle via horizontal spans."""
        r = int(r)
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - half, cy + dy, half * 2 + 1, 1, col)

    def ring(self, cx, cy, r, col, thick=1):
        """Circle outline, drawn as concentric rings."""
        for rr in range(r, r - thick, -1):
            if rr < 0:
                continue
            for dy in range(-rr, rr + 1):
                half = int((rr * rr - dy * dy) ** 0.5)
                self.rect(cx - half, cy + dy, 1, 1, col)
                self.rect(cx + half, cy + dy, 1, 1, col)

    def ellipse(self, cx, cy, rx, ry, col):
        for dy in range(-ry, ry + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            half = int(rx * (t ** 0.5)) if t > 0 else 0
            self.rect(cx - half, cy + dy, half * 2 + 1, 1, col)

    def arc(self, cx, cy, r, a0, a1, col, thick=2):
        """Arc (degrees, 0 = east, clockwise positive) as short chords."""
        steps = max(4, int(abs(a1 - a0) / 6.0) + 1)
        prev = None
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            px = int(cx + r * math.cos(a))
            py = int(cy + r * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, col, thick)
            prev = (px, py)

    def polygon(self, pts, col):
        """Scanline fill (even-odd) of a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = max(0, min(ys)), min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    t = (y - yy0) / float(yy1 - yy0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[i] + 0.5), int(xs[i + 1] + 0.5)
                if xb > xa:
                    self.rect(xa, y, xb - xa, 1, col)

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient, one row slice per line."""
        for i in range(h):
            t = i / max(1, h - 1)
            col = tuple(int(top[c] + (bottom[c] - top[c]) * t)
                        for c in range(3))
            self.rect(x, y + i, w, 1, col)

    def outline(self, x, y, w, h, col, thick=1):
        self.rect(x, y, w, thick, col)
        self.rect(x, y + h - thick, w, thick, col)
        self.rect(x, y, thick, h, col)
        self.rect(x + w - thick, y, thick, h, col)


def star_points(cx, cy, r_out, r_in, rot=-90.0):
    """Five-point star vertices, alternating outer/inner radius."""
    pts = []
    for i in range(10):
        ang = math.radians(rot + i * 36.0)
        r = r_out if i % 2 == 0 else r_in
        pts.append((int(cx + r * math.cos(ang)),
                    int(cy + r * math.sin(ang))))
    return pts


def png_bytes(cv):
    """Encode the canvas as a PNG (color type 2, filter 0 per row)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# -------------------------------------------------------------------- font
# Hand-made 5x7 bitmap font. Each glyph is 7 rows of 5 cells ('1' = on).
# Proportional advances: default 6, narrow 4, wide 7, space 4.
# Glyphs verified by rendering: E has top, middle and bottom bars;
# g and y carry descenders into rows 5-6; z is a full diagonal.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01110", "10001", "10001", "01111", "00010", "01100"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00010"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10001", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "10001", "01111", "00110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "–": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "•": ("00000", "00000", "01110", "11111", "11111", "01110", "00000"),
    "·": ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    "°": ("01100", "10010", "01100", "00000", "00000", "00000", "00000"),
    "€": ("01110", "10001", "10000", "11110", "10000", "10001", "01110"),
    "×": ("00000", "00000", "10001", "01110", "01110", "10001", "00000"),
    "’": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "“": ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "”": ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
}

# Every glyph is exactly 7 rows; descenders live in rows 5-6.
_NARROW = set("il1Ijt.,:;'\"()![]")
_WIDE = set("mwMW")


def adv(ch):
    """Advance width of one character, in font units."""
    if ch == " ":
        return 4
    if ch in _NARROW:
        return 4
    if ch in _WIDE:
        return 7
    return 6


def text_w(text, scale, tracking=0):
    """Pixel width of text at the given scale."""
    w = 0
    for ch in text:
        w += adv(ch) * scale + tracking
    return w - tracking if text else 0


def draw_glyph(cv, x, y, ch, scale, col):
    """Draw one glyph; runs of on-pixels become filled rectangles."""
    rows = FONT.get(ch)
    if rows is None:
        rows = FONT["?"]
    for r, row in enumerate(rows):
        c = 0
        while c < 5:
            if row[c] == "1":
                c0 = c
                while c + 1 < 5 and row[c + 1] == "1":
                    c += 1
                cv.rect(x + c0 * scale, y + r * scale,
                        (c - c0 + 1) * scale, scale, col)
            c += 1


def draw_text(cv, x, y, text, scale, col, bold=False, tracking=0,
              align="left", box_w=None):
    """Draw text; align left/center/right within box_w when given."""
    w = text_w(text, scale, tracking)
    if align == "center" and box_w is not None:
        x += (box_w - w) // 2
    elif align == "right" and box_w is not None:
        x += box_w - w
    cx = x
    for ch in text:
        draw_glyph(cv, cx, y, ch, scale, col)
        if bold:
            draw_glyph(cv, cx + 1, y, ch, scale, col)
        cx += adv(ch) * scale + tracking
    return w


def draw_tracked(cv, x, y, text, scale, col, tracking=2):
    return draw_text(cv, x, y, text, scale, col, tracking=tracking)


def wrap_text(text, scale, max_w, tracking=0):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if text_w(trial, scale, tracking) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
    return lines


# --------------------------------------------------------------------- map
# Hand-drawn continent outlines (lon, lat vertex lists) for the dotted
# world map. Coarse on purpose: the map is a locator, not a chart.
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

LAND = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE, UK, ASIA,
        INDONESIA, BORNEO, NEW_GUINEA, PHILIPPINES, JAPAN, AUSTRALIA,
        NEW_ZEALAND]

REGION_COLORS = {
    "americas": PIN_RED, "asia": PIN_PURPLE, "europe": PIN_BLUE,
    "mideast": PIN_ORANGE, "africa": PIN_GREEN, "oceania": PIN_TEAL,
}


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xinters = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xinters:
                inside = not inside
        j = i
    return inside


def on_land(lon, lat):
    return any(point_in_poly(lon, lat, p) for p in LAND)


def draw_map(cv, x, y, w, h, pins):
    """Dotted world map with numbered pins (num, (lon, lat, region))."""
    cv.rect(x, y, w, h, MAP_BG)
    cv.outline(x, y, w, h, (150, 150, 140), 1)
    lon0, lon1, lat0, lat1 = -180.0, 180.0, 83.0, -58.0
    lon = -180.0
    while lon <= 180.0:
        lat = 83.0
        while lat >= -58.0:
            if on_land(lon, lat):
                px = x + (lon - lon0) / (lon1 - lon0) * w
                py = y + (lat0 - lat) / (lat0 - lat1) * h
                cv.circle(int(px), int(py), 2, DOT)
            lat -= 3.0
        lon += 3.0
    for num, (plon, plat, region) in pins:
        px = x + (plon - lon0) / (lon1 - lon0) * w
        py = y + (lat0 - plat) / (lat0 - lat1) * h
        col = REGION_COLORS[region]
        cv.circle(int(px), int(py), 7, col)
        cv.ring(int(px), int(py), 7, WHITE, 1)
        s = str(num)
        sw = text_w(s, 1)
        draw_text(cv, int(px - sw / 2), int(py - 4), s, 1, WHITE)


# ------------------------------------------------------------------- flags
def draw_flag(cv, x, y, w, h, kind):
    """Small flag, drawn with rectangles (and stars for China)."""
    if kind == "us":
        for i in range(7):
            cv.rect(x, y + i * h // 7, w, h // 7 + 1,
                    (178, 32, 44) if i % 2 == 0 else WHITE)
        cw, ch = w * 2 // 5, h * 4 // 7
        cv.rect(x, y, cw, ch, (30, 50, 110))
        for r in range(3):
            for c in range(4):
                cv.rect(x + 3 + c * (cw // 4), y + 3 + r * (ch // 3), 2, 2,
                        WHITE)
    elif kind == "china":
        cv.rect(x, y, w, h, (200, 30, 30))
        cv.polygon(star_points(x + w // 4, y + h // 3, 7, 3),
                   (255, 215, 0))
        for sx, sy in ((x + w * 3 // 5, y + h // 5),
                       (x + w * 3 // 4, y + h * 2 // 5),
                       (x + w * 3 // 4, y + h * 3 // 5),
                       (x + w * 3 // 5, y + h * 4 // 5)):
            cv.polygon(star_points(sx, sy, 3, 1), (255, 215, 0))
    elif kind == "russia":
        cv.rect(x, y, w, h // 3 + 1, WHITE)
        cv.rect(x, y + h // 3, w, h // 3 + 1, (30, 80, 170))
        cv.rect(x, y + 2 * h // 3, w, h - 2 * h // 3, (200, 30, 30))


# ------------------------------------------------------------------- icons
# Small flat pictograms for the medium stories: a coloured square with
# a white glyph drawn from basic shapes. All coordinates are in the
# icon's own 40x40 box (the tile draws them at 36x36).
ICON_COLORS = {
    "virus": (178, 60, 50), "globe": (40, 120, 130), "cross": (60, 140, 70),
    "chart": (40, 110, 60), "tent": (150, 90, 50), "building": (70, 90, 130),
    "ballot": (110, 70, 150), "factory": (200, 110, 40), "plane": (40, 60, 110),
    "gavel": (140, 50, 50), "bank": (30, 50, 90), "ship": (60, 100, 140),
    "storm": (90, 100, 120), "bridge": (38, 84, 160), "blast": (178, 32, 44),
    "game": (110, 70, 150), "probe": (20, 90, 110), "chip": (30, 30, 40),
    "sun": (200, 140, 30), "doc": (90, 90, 90),
}


def draw_icon(cv, x, y, s, kind):
    """Draw an s-by-s icon at (x, y)."""
    cv.rect(x, y, s, s, ICON_COLORS.get(kind, (90, 90, 90)))
    wcol = WHITE
    c = s / 2
    if kind == "virus":
        cv.circle(x + int(c), y + int(c), 9, wcol)
        for dx, dy in ((-13, 0), (13, 0), (0, -13), (0, 13),
                       (-9, -9), (9, 9)):
            cv.circle(x + int(c + dx), y + int(c + dy), 3, wcol)
    elif kind == "globe":
        cv.ring(x + int(c), y + int(c), 14, wcol, 2)
        cv.ellipse(x + int(c), y + int(c), 6, 14, wcol)
        cv.line(x + 8, y + int(c), x + s - 8, y + int(c), wcol, 2)
    elif kind == "cross":
        cv.rect(x + int(c) - 5, y + 10, 10, s - 20, wcol)
        cv.rect(x + 10, y + int(c) - 5, s - 20, 10, wcol)
    elif kind == "chart":
        for i, hh in enumerate((12, 20, 28)):
            bx = x + 9 + i * 11
            cv.rect(bx, y + s - 8 - hh, 7, hh, wcol)
    elif kind == "tent":
        cv.polygon([(x + 6, y + s - 8), (x + int(c), y + 10),
                    (x + s - 6, y + s - 8)], wcol)
        cv.polygon([(x + int(c) - 4, y + s - 8), (x + int(c), y + s - 20),
                    (x + int(c) + 4, y + s - 8)], (60, 60, 60))
    elif kind in ("building", "bank"):
        cv.polygon([(x + 6, y + 12), (x + int(c), y + 6),
                    (x + s - 6, y + 12)], wcol)
        cv.rect(x + 8, y + 14, s - 16, 4, wcol)
        for i in range(4):
            bx = x + 10 + i * 9
            cv.rect(bx, y + 20, 4, s - 32, wcol)
        cv.rect(x + 6, y + s - 12, s - 12, 4, wcol)
    elif kind == "ballot":
        cv.rect(x + 10, y + 16, s - 20, s - 24, wcol)
        cv.line(x + 14, y + 16, x + s - 14, y + 16, wcol, 2)
        cv.polygon([(x + int(c) - 8, y + 8), (x + int(c) + 2, y + 14),
                    (x + int(c) - 2, y + 14), (x + int(c) - 12, y + 8)],
                   wcol)
    elif kind == "factory":
        cv.polygon([(x + 8, y + s - 8), (x + 8, y + 20), (x + 16, y + 14),
                    (x + 24, y + 20), (x + 32, y + 14), (x + s - 8, y + 20),
                    (x + s - 8, y + s - 8)], wcol)
        cv.rect(x + s - 16, y + 8, 4, 12, wcol)
    elif kind == "plane":
        cv.polygon([(x + 6, y + int(c) + 4), (x + s - 8, y + int(c) - 10),
                    (x + s - 8, y + int(c) - 4), (x + 16, y + int(c) + 8),
                    (x + 12, y + int(c) + 12), (x + 6, y + int(c) + 10)],
                   wcol)
    elif kind == "gavel":
        cv.rect(x + 10, y + 12, s - 24, 8, wcol)
        cv.line(x + int(c) + 2, y + 20, x + s - 10, y + s - 10, wcol, 4)
    elif kind == "ship":
        cv.polygon([(x + 6, y + s - 14), (x + s - 6, y + s - 14),
                    (x + s - 12, y + s - 6), (x + 12, y + s - 6)], wcol)
        cv.rect(x + 12, y + s - 26, 8, 12, wcol)
        cv.rect(x + 22, y + s - 22, 8, 8, wcol)
    elif kind == "storm":
        cv.ellipse(x + 16, y + 20, 8, 6, wcol)
        cv.ellipse(x + 26, y + 18, 8, 6, wcol)
        for i in range(3):
            bx = x + 13 + i * 9
            cv.line(bx, y + 30, bx - 2, y + 38, wcol, 2)
    elif kind == "bridge":
        cv.rect(x + 6, y + 24, 10, 3, wcol)
        cv.rect(x + 24, y + 24, 10, 3, wcol)
        cv.arc(x + 11, y + 19, 6, 180, 360, wcol, 2)
        cv.arc(x + 29, y + 19, 6, 180, 360, wcol, 2)
        cv.polygon([(x + 17, y + 25), (x + 21, y + 33), (x + 24, y + 31),
                    (x + 20, y + 24)], wcol)
        cv.circle(x + 31, y + 10, 4, (255, 210, 110))
    elif kind == "blast":
        cx, cy = x + s // 2, y + s // 2
        cv.polygon([(cx, cy - 14), (cx + 4, cy - 4), (cx + 14, cy - 6),
                    (cx + 7, cy + 2), (cx + 12, cy + 10), (cx + 2, cy + 8),
                    (cx, cy + 15), (cx - 3, cy + 7), (cx - 13, cy + 9),
                    (cx - 7, cy + 1), (cx - 14, cy - 5), (cx - 4, cy - 5)],
                   (255, 210, 110))
        cv.circle(cx, cy, 4, wcol)
    elif kind == "game":
        cv.rect(x + 6, y + 14, s - 12, 16, wcol)
        cv.circle(x + 12, y + 20, 3, (110, 70, 150))
        cv.circle(x + 28, y + 20, 3, (110, 70, 150))
        cv.line(x + 12, y + 27, x + 17, y + 27, (110, 70, 150), 2)
        cv.line(x + 24, y + 26, x + 29, y + 26, (110, 70, 150), 2)
    elif kind == "probe":
        cv.arc(x + 17, y + 17, 9, 90, 270, wcol, 3)
        cv.line(x + 17, y + 17, x + 30, y + 30, wcol, 3)
        cv.rect(x + 28, y + 28, 6, 6, wcol)
        for dx, dy in ((30, 8), (34, 14), (26, 12)):
            cv.circle(x + dx, y + dy, 1, (255, 210, 110))
    elif kind == "chip":
        cv.rect(x + 12, y + 12, s - 24, s - 24, wcol)
        cv.rect(x + 17, y + 17, s - 34, s - 34, wcol)
        for i in range(3):
            cv.line(x + 14 + i * 6, y + 6, x + 14 + i * 6, y + 12, wcol, 2)
            cv.line(x + 14 + i * 6, y + s - 12, x + 14 + i * 6, y + s - 6,
                    wcol, 2)
    elif kind == "sun":
        cv.circle(x + int(c), y + int(c), 9, wcol)
        for dx, dy in ((-13, 0), (13, 0), (0, -13), (0, 13),
                       (-9, -9), (9, -9), (-9, 9), (9, 9)):
            cv.line(x + int(c), y + int(c), x + int(c + dx), y + int(c + dy),
                    wcol, 2)
    else:  # doc
        cv.rect(x + 12, y + 8, s - 24, s - 16, wcol)
        for i in range(3):
            ly = y + 15 + i * 8
            cv.line(x + 16, ly, x + s - 16, ly, wcol, 2)


# -------------------------------------------------------------- panel art
def panel_shenzhen(cv, x, y, w, h):
    """Dusk over Shenzhen: orange-purple sky, sun, skyline, three flags."""
    ground = y + int(h * 0.72)
    cv.vgrad(x, y, w, ground - y, (232, 128, 52), (146, 68, 116))
    sx, sy, sr = x + w - 52, y + 26, 13
    cv.circle(sx, sy, sr, (255, 226, 140))
    cv.rect(x, ground, w, y + h - ground, (26, 28, 58))
    heights = [26, 40, 32, 48, 36, 56, 30, 44, 38, 52, 28, 42]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bh = bh * h // 150
        bx = x + i * bw
        cv.rect(bx + 1, ground - bh, bw - 2, bh, (26, 28, 58))
        if i % 3 == 0:
            cv.rect(bx + bw // 2 - 1, ground - bh - 8, 2, 8, (26, 28, 58))
        for wy in range(ground - bh + 6, ground - 4, 9):
            for wx in (bx + 5, bx + bw - 9):
                if (wx + wy) % 3 == 0:
                    cv.rect(wx, wy, 2, 2, (255, 210, 110))
    kinds = ["us", "china", "russia"]
    fw, fh = 56, 36
    gap = (w - len(kinds) * fw) // (len(kinds) + 1)
    for i, kind in enumerate(kinds):
        fx = x + gap + i * (fw + gap)
        fy = ground - fh - 16
        cv.rect(fx + fw // 2 - 1, fy, 2, ground - fy, CREAM)
        draw_flag(cv, fx, fy, fw, fh, kind)


def panel_gaza_night(cv, x, y, w, h):
    """Night over central Gaza: tents, searchlights, flare, smoke."""
    horizon = y + int(h * 0.62)
    cv.vgrad(x, y, w, horizon - y, (8, 18, 42), (30, 50, 92))
    for fx, fy, r in ((0.05, 0.10, 1), (0.13, 0.22, 1), (0.22, 0.08, 1),
                      (0.32, 0.16, 2), (0.40, 0.06, 1), (0.50, 0.18, 1),
                      (0.60, 0.08, 2), (0.70, 0.20, 1), (0.79, 0.10, 1),
                      (0.89, 0.22, 1), (0.96, 0.12, 1), (0.17, 0.34, 1),
                      (0.53, 0.32, 1), (0.76, 0.34, 1)):
        cv.circle(x + int(fx * w), y + int(fy * h), r, (235, 238, 245))
    cv.rect(x, horizon, w, y + h - horizon, (24, 22, 20))
    for fx, fw, fh in ((0.05, 0.15, 0.20), (0.23, 0.19, 0.26),
                       (0.47, 0.17, 0.22), (0.68, 0.20, 0.28),
                       (0.86, 0.15, 0.18)):
        tx, tw = x + int(fx * w), int(fw * w)
        th = int(fh * h)
        cv.polygon([(tx, horizon), (tx + tw // 2, horizon - th),
                    (tx + tw, horizon)], (120, 110, 92))
        cv.polygon([(tx + tw // 2 - 3, horizon),
                    (tx + tw // 2, horizon - th // 2),
                    (tx + tw // 2 + 3, horizon)], (40, 36, 30))
    for ex, ey in ((0.50, 0.12), (0.70, 0.26)):
        cv.polygon([(x + int(0.07 * w), horizon - 6),
                    (x + int(ex * w), y + int(ey * h) - 3),
                    (x + int(ex * w), y + int(ey * h) + 3)],
                   (220, 220, 190))
    gx, gy = x + int(0.84 * w), horizon - 6
    for frac, col in ((1.00, (198, 88, 28)), (0.72, (228, 128, 38)),
                      (0.48, (248, 188, 78)), (0.26, (255, 230, 150))):
        cv.circle(gx, gy, max(2, int(22 * frac * h / 100)), col)
    for px, py, pr in ((-0.05, -0.20, 10), (0.0, -0.30, 12),
                       (0.05, -0.22, 9), (0.01, -0.40, 8)):
        cv.circle(gx + int(px * w), gy + int(py * h), max(2, pr * h // 100),
                  (88, 88, 96))
    cv.line(gx - 30, gy - 30, gx + 6, gy - 8, (255, 240, 180), 2)


def panel_ipo(cv, x, y, w, h):
    """Nasdaq debut: dark board, rising green bars, gold $97.17 tag."""
    cv.vgrad(x, y, w, h, (10, 22, 48), (24, 52, 92))
    for gy in (0.22, 0.44, 0.66):
        cv.hline(x + 8, y + int(gy * h), w - 16, (60, 80, 120), 1)
    bars = [18, 26, 22, 34, 30, 44, 40, 56]
    bw = max(4, w // 12)
    gap = max(2, w // 48)
    bx0 = x + 10
    base = y + h - 14
    for i, bh in enumerate(bars):
        bx = bx0 + i * (bw + gap)
        bh_px = bh * h // 100
        cv.rect(bx, base - bh_px, bw, bh_px, (46, 160, 90))
    pts = [(bx0 + 4, base - 18), (bx0 + int(0.30 * w), base - 34),
           (bx0 + int(0.55 * w), base - 30), (bx0 + int(0.80 * w), base - 56),
           (bx0 + w - 24, base - 62)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], (120, 220, 150), 3)
    ex, ey = pts[-1]
    cv.polygon([(ex, ey), (ex - 14, ey - 4), (ex - 12, ey + 8)],
               (120, 220, 150))
    tag = "$97.17"
    tscale = 3 if text_w(tag, 3) <= w - 20 else 2
    draw_text(cv, x + w - text_w(tag, tscale) - 8, y + 8, tag, tscale,
              GOLD_LT)
    draw_text(cv, x + w - text_w("CLOSE, +17%", 1) - 8,
              y + 8 + tscale * 7 + 4, "CLOSE, +17%", 1, WHITE)


def panel_cyclone(cv, x, y, w, h):
    """Cyclone Akvan over the Bay of Bengal: spiral bands, rain, sea."""
    cv.vgrad(x, y, w, h, (52, 74, 96), (140, 158, 172))
    cx, cy = x + int(w * 0.42), y + int(h * 0.44)
    # spiral cloud bands: concentric arcs, pale grey-blue
    for r, col in ((46, (200, 212, 220)), (36, (216, 226, 232)),
                   (26, (228, 236, 240)), (16, (240, 244, 246))):
        cv.ring(cx, cy, r, col, 5)
    cv.circle(cx, cy, 9, (240, 244, 246))
    # rain streaks, slanted
    for rx in range(0, w, 18):
        ry = y + (rx * 7) % (h - 30)
        cv.line(x + rx, ry, x + rx - 6, ry + 16, (190, 205, 215), 2)
    # sea at the bottom with white-capped waves
    sea = y + int(h * 0.78)
    cv.rect(x, sea, w, y + h - sea, (38, 84, 120))
    for wy in (sea + 6, sea + 14):
        for wx in range(0, w, 26):
            cv.arc(x + wx + 11, wy, 9, 200, 340, (220, 235, 245), 2)
    # a bending palm on the shore
    px, py = x + w - 34, sea + 2
    cv.line(px, py, px + 6, py - 26, (70, 50, 30), 3)
    for dx, dy in ((-14, -30), (-4, -34), (8, -32), (16, -26), (18, -20)):
        cv.line(px + 6, py - 26, px + 6 + dx, py - 26 + dy, (40, 120, 60), 2)


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
VIOLATIONS = []


def check_fit(label, width, max_w):
    if width > max_w:
        VIOLATIONS.append("%s: %dpx > %dpx" % (label, width, max_w))


def draw_page():
    cv = Canvas(W, H, PAPER)

    # ---- dark navy masthead ----
    cv.rect(0, 0, W, 106, NAVY)
    draw_tracked(cv, MARGIN, 13, "THE DAY IN WORLD NEWS", 2, GOLD_LT, 2)
    right = "48 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE"
    check_fit("masthead right", text_w(right, 2, 2), CW)
    draw_tracked(cv, W - MARGIN - text_w(right, 2, 2), 13, right, 2,
                 GOLD_LT, 2)
    check_fit("masthead title", text_w("Friday 20 November 2026", 5), CW)
    draw_text(cv, MARGIN, 30, "Friday 20 November 2026", 5, WHITE)
    draw_text(cv, MARGIN, 86,
              "Every story on this page happened, or was first reported, on this day.",
              2, (205, 205, 195))
    cv.rect(0, 106, W, 3, GOLD)

    # ---- three rich panels with caption strips ----
    px = [MARGIN, MARGIN + 312 + 16, MARGIN + 2 * (312 + 16)]
    py, ph = 116, 100
    panels = [panel_shenzhen, panel_cyclone, panel_ipo]
    for i, fn in enumerate(panels):
        x = px[i]
        fn(cv, x, py, 312, ph)
        cv.rect(x, py + ph - 17, 312, 17, NAVY_DARK)
        draw_tracked(cv, x + 6, py + ph - 13, PANEL_CAPTIONS[i], 1,
                     WHITE, 1)
        cv.outline(x, py, 312, ph, INK, 2)

    # ---- three featured stories under the panels ----
    fy = 224
    for i, st in enumerate(FEATURED):
        x = px[i]
        cx, cy = x + 10, fy + 9
        cv.circle(cx, cy, 9, RED)
        s = str(st["num"])
        draw_text(cv, cx - text_w(s, 1) // 2, cy - 4, s, 1, WHITE)
        draw_tracked(cv, x + 24, fy + 2, st["kicker"], 2, RED, 1)
        yy = fy + 24
        hlines = wrap_text(st["headline"], 3, 312)
        if len(hlines) > 3:
            VIOLATIONS.append("featured %d headline >3 lines"
                              % st["num"])
        for ln in hlines[:3]:
            draw_text(cv, x, yy, ln, 3, INK)
            yy += 21
        yy += 2
        dlines = wrap_text(st["deck"], 2, 312)
        if len(dlines) > 3:
            VIOLATIONS.append("featured %d deck >3 lines" % st["num"])
        for ln in dlines[:3]:
            draw_text(cv, x, yy, ln, 2, DARKGRAY)
            yy += 14

    cv.hline(MARGIN, 362, CW, RULE, 2)

    # ---- ten medium tiles, 5 columns x 2 rows ----
    colw, gap = 185, 10
    rows_y = [372, 476]
    for idx, st in enumerate(MEDIUM):
        r, c = divmod(idx, 5)
        x = MARGIN + c * (colw + gap)
        y = rows_y[r]
        draw_icon(cv, x, y, 36, st["icon"])
        kw = text_w(st["kicker"], 1, 1)
        if kw > colw - 42:
            VIOLATIONS.append(("kicker too wide", st["num"], st["kicker"],
                               kw))
        draw_tracked(cv, x + 42, y + 2, st["kicker"], 1, RED, 1)
        yy = y + 17
        hlines = wrap_text(st["headline"], 2, colw - 42)
        if len(hlines) > 3:
            VIOLATIONS.append(("headline >3 lines", st["num"],
                               st["headline"], len(hlines)))
        for ln in hlines[:3]:
            draw_text(cv, x + 42, yy, ln, 2, INK)
            yy += 15
        yy = y + 64
        dlines = wrap_text(st["deck"], 1, colw)
        if len(dlines) > 2:
            VIOLATIONS.append(("deck >2 lines", st["num"], st["deck"],
                               len(dlines)))
        for ln in dlines[:2]:
            draw_text(cv, x, yy, ln, 1, DARKGRAY)
            yy += 12

    cv.hline(MARGIN, 572, CW, RULE, 2)

    # ---- BY THE NUMBERS strip ----
    draw_text(cv, MARGIN, 580, "BY THE", 2, RED)
    draw_text(cv, MARGIN, 596, "NUMBERS", 2, RED)
    ncol_w, ncol_gap, nx0 = 210, 8, 130
    for i, (num, label) in enumerate(NUMBERS):
        nx = nx0 + i * (ncol_w + ncol_gap)
        scale = 3 if text_w(num, 3) <= 200 else 2
        draw_text(cv, nx, 578, num, scale, NAVY)
        yy = 610
        for ln in wrap_text(label, 1, ncol_w):
            draw_text(cv, nx, yy, ln, 1, DARKGRAY)
            yy += 9

    cv.hline(MARGIN, 632, CW, RULE, 2)

    # ---- bottom: map + region bars + also list ----
    by = 640
    draw_tracked(cv, MARGIN, by, "WHERE IT HAPPENED", 2, INK, 2)
    draw_text(cv, MARGIN, by + 18, "Numbered dots mark stories 1-13",
              1, GRAY)
    also_title = "ALSO ON FRIDAY 20 NOVEMBER \u2014 35 MORE"
    check_fit("also title", text_w(also_title, 2, 1), W - MARGIN - 486)
    draw_tracked(cv, 486, by, also_title, 2, INK, 1)

    pins = [(s["num"], s["pin"]) for s in FEATURED + MEDIUM]
    draw_map(cv, MARGIN, by + 38, 442, 240, pins)

    # STORIES BY REGION bars under the map (2 rows x 3 cells).
    max_n = max(n for _, n, _ in REGIONS)
    for i, (name, n, col) in enumerate(REGIONS):
        r, c = divmod(i, 3)
        bx = MARGIN + c * 148
        yy = by + 284 + r * 22
        cv.circle(bx + 4, yy + 4, 4, col)
        draw_text(cv, bx + 11, yy, name, 1, INK)
        cnt = str(n)
        draw_text(cv, bx + 147 - text_w(cnt, 1), yy, cnt, 1, INK)
        cv.rect(bx, yy + 13, 100, 5, (225, 220, 205))
        if n:
            cv.rect(bx, yy + 13, max(1, int(100 * n / max_n)), 5, col)

    # ALSO list, two columns of 18/17, 13px pitch.
    start_num = 14
    half = (len(ALSO) + 1) // 2
    for col_i, chunk in enumerate((ALSO[:half], ALSO[half:])):
        cx = 486 + col_i * 260
        yy = by + 38
        for j, item in enumerate(chunk):
            num = start_num + (col_i * half + j)
            draw_text(cv, cx, yy, str(num), 1, RED, bold=True)
            place, sep, rest = item.partition(": ")
            tx = cx + 24
            if sep:
                full_w = (text_w(place + ":", 1, 0, )
                          + text_w(rest, 1))
                if full_w > 226:
                    VIOLATIONS.append((num, item, full_w))
                draw_text(cv, tx, yy, place + ":", 1, INK, bold=True)
                tx += text_w(place + ": ", 1)
                draw_text(cv, tx, yy, rest, 1, INK)
            else:
                if text_w(item, 1) > 226:
                    VIOLATIONS.append((num, item, text_w(item, 1)))
                draw_text(cv, tx, yy, item, 1, INK)
            yy += 13

    if VIOLATIONS:
        print("LAYOUT VIOLATIONS:")
        for v in VIOLATIONS:
            print("  ", v)
        sys.exit(1)

    # ---- footer ----
    cv.hline(MARGIN, 974, CW, RULE, 1)
    draw_text(cv, MARGIN, 980, FOOTER1, 1, GRAY)
    draw_text(cv, MARGIN, 994, FOOTER2, 1, GRAY)

    total = len(FEATURED) + len(MEDIUM) + len(ALSO)
    if total != 48:
        print("STORY COUNT %d != 48" % total)
        sys.exit(1)
    return cv


def main():
    cv = draw_page()
    data = png_bytes(cv)
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
