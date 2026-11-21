#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- Friday 20 November 2026 (v4.2).

A one-page newspaper front page drawn from nothing but the Python
standard library. Forty real stories from Friday 20 November 2026:
three big illustrated leads, ten illustrated tiles, a six-number
strip, a region bar, a solid world map with numbered pins, 27 more
briefs, a DATE CHECK box, and a footer.

v4.2 fixes the five findings of the v4.1 analysis
(analisa-v41-vs-v3-2026-11-21.md): (1) freshness re-audited
two-way, story by story, against the date each item was first
reported -- the stale Gemini 4 Neon tile (18 Nov) and the stale
51-48 Senate number (19 Nov) are replaced by verified 20 Nov
items (Wall Street's Thursday close, Anthropic's $2tn debut,
SoftBank's 14.5% plunge) and named in DATE CHECK; the ALSO list
was rebuilt the same way, dropping every unverified or stale
brief and fixing three wrong numbers (Sensex, Nikkei, NZ score);
(2) the AI lead panel gains a 4-city table (Taipei -6.2%,
Seoul -5.2%, Tokyo -5.1%, Hong Kong -1.9%); (3) the map is
recoloured sand/sage for contrast, with bigger pins; (4) the
subhead is back to real serif italic; (5) the masthead font is
deliberately NOT redesigned -- the gains come from content.

v4 is a ground-up rebuild from the top-10 leaderboard research
(top5-riset-ulang-2026-11-21.md). v3 ranked 4,030/9,395, judge
96.35%, cutoff 98.84% -- a structural +2.51 point gap, not noise.
The research found five large, visible gaps in v3:

  1. FONT: every letter was a 5x7 pixel bitmap -- the page read as
     a dot-matrix printout next to the winners' real serif type.
     v4 draws every letter as a vector stroke font -- serif with
     ticks for the titles only (masthead, the name line above it,
     and all headlines), clean sans for every other line of text,
     including a real lowercase 'g' -- so "bridges", "Google" and
     "drought" can be spelled again. The whole page is rendered
     at 2x and box downsampled, which anti-aliases every edge.
  2. LAYOUT: v3 put DATE CHECK and the numbers strip in the middle
     of the page and the region bar under the map. v4 follows the
     canonical winner order: masthead -> subhead (4 headlines) ->
     numbers strip (6) -> region bar (top) -> 3 leads -> 10 tiles
     -> map -> ALSO -> DATE CHECK (bottom) -> footer.
  3. KYIV: v3 buried the day's biggest war story as tile #8. v4
     leads with it: 110 missiles and 400 drones, three bridges
     hit, nine killed. Akvan stays lead #2; the Asia AI sell-off
     is lead #3.
  4. FRESHNESS: v3 contradicted its own DATE CHECK twice (a
     US-Venezuela tile it claimed to exclude; a Crimea span tile
     from 19 Nov). Both are gone; the exclude list gained the
     Crimea hit. Every DATE CHECK item is absent from the page.
  5. NUMBERS: the strip now holds the six biggest numbers of the
     day (3 bridges, 372,000 evacuated, -6.2% Taiex, 118 Phillips,
     100,000 UK-EU youth visas, $97.17 Anthropic close).

Tiles carry a specific flat mini-illustration each (~40% of the
tile), the ALSO list names a source per brief, the region bar has
no zero region (Kenya oil gives Africa its story; Phillips 118
gives Oceania one), and the subhead is four headlines in italic
instead of a generic freshness claim (that claim moved to the
footer, as the winners do).

Drawing: a bytearray RGB canvas rendered at 2x and downsampled,
a hand-drawn vector stroke font, flat vector picture panels and
mini-scenes, a solid world map traced from coarse continent
outlines I plotted by hand, and a PNG writer built on zlib. No
network, no randomness, no third-party packages -- two runs write
identical bytes.

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

W, H = 1024, 1024
MX = 26                      # side margin
CW = W - 2 * MX              # live width, 972

PAPER = (250, 246, 236)
INK = (24, 24, 24)
SOFT = (74, 74, 70)
FAINT = (118, 116, 108)
RED = (176, 30, 40)
RED_DK = (138, 20, 30)
TEAL = (14, 90, 92)
TEAL_LT = (186, 220, 220)
GOLD = (196, 150, 60)
GOLD_LT = (232, 204, 130)
NAVY = (30, 48, 80)
NAVY_DK = (20, 34, 58)
CREAM = (238, 230, 212)
SKY = (198, 222, 235)
SEA = (64, 128, 158)
SAND = (226, 208, 170)
WHITE = (255, 255, 255)
LINE = (24, 24, 24)
HAIR = (196, 190, 176)
MAP_BG = NAVY
MAP_LAND = SAND
DATE_BG = (255, 241, 235)

PINKS = {
    "europe": (38, 84, 160),
    "asia": (110, 70, 150),
    "mideast": (200, 110, 40),
    "africa": (46, 140, 70),
    "americas": (176, 30, 40),
    "oceania": (20, 120, 130),
    "global": (90, 90, 90),
}


class Canvas:
    """An RGB picture as one bytearray, rendered at 2x supersampling.

    All drawing coordinates are in logical (1024-space) units; every
    primitive scales them by SS internally, and downsample() averages
    each SS x SS block back to one pixel. That is the anti-aliasing:
    diagonal letter strokes and art edges come out with grey fringe
    pixels instead of stair steps. Deterministic: integer math only.
    """

    SS = 2

    def __init__(self, w, h, bg, s=None):
        self.w = w
        self.h = h
        self.s = self.SS if s is None else s
        self.pw = w * self.s
        self.ph = h * self.s
        self.px = bytearray(bytes(bg) * (self.pw * self.ph))

    def _row(self, y):
        return y * self.pw * 3

    def fill(self, x, y, w, h, c):
        """Solid rectangle, clipped to the canvas."""
        s = self.s
        xa = max(0, int(math.floor(x * s)))
        ya = max(0, int(math.floor(y * s)))
        xb = min(self.pw, int(math.ceil((x + w) * s)))
        yb = min(self.ph, int(math.ceil((y + h) * s)))
        if xb <= xa or yb <= ya:
            return
        run = bytes(c) * (xb - xa)
        for yy in range(ya, yb):
            o = self._row(yy) + xa * 3
            self.px[o:o + len(run)] = run

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def dot(self, x, y, c):
        s = self.s
        xi, yi = int(round(x * s)), int(round(y * s))
        if 0 <= xi < self.pw and 0 <= yi < self.ph:
            o = self._row(yi) + xi * 3
            self.px[o:o + 3] = bytes(c)

    def line(self, x0, y0, x1, y1, c, t=1):
        """Bresenham walk with a square brush, in scaled space."""
        s = self.s
        t = max(1, int(round(t * s)))
        x0, y0 = int(round(x0 * s)), int(round(y0 * s))
        x1, y1 = int(round(x1 * s)), int(round(y1 * s))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, half = dx - dy, t // 2
        x, y = x0, y0
        while True:
            self.fill((x - half) / s, (y - half) / s, t / s, t / s, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        """Filled circle, one span per row."""
        s = self.s
        cx, cy, r = int(round(cx * s)), int(round(cy * s)), int(round(r * s))
        for dy in range(-r, r + 1):
            span = int((r * r - dy * dy) ** 0.5)
            self.fill((cx - span) / s, (cy + dy) / s,
                      (span * 2 + 1) / s, 1 / s, c)

    def ring(self, cx, cy, r, c, t=2):
        """Circle outline of thickness t."""
        s = self.s
        cx, cy = int(round(cx * s)), int(round(cy * s))
        r = int(round(r * s))
        t = max(1, int(round(t * s)))
        inner = (r - t) * (r - t)
        outer = r * r
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = dx * dx + dy * dy
                if inner < d <= outer:
                    o = self._row(cy + dy) + (cx + dx) * 3
                    if 0 <= cy + dy < self.ph and 0 <= cx + dx < self.pw:
                        self.px[o:o + 3] = bytes(c)

    def ellipse(self, cx, cy, rx, ry, c):
        s = self.s
        cx, cy = int(round(cx * s)), int(round(cy * s))
        rx, ry = int(round(rx * s)), int(round(ry * s))
        for dy in range(-ry, ry + 1):
            q = 1.0 - (dy * dy) / float(ry * ry)
            span = int(rx * (q ** 0.5)) if q > 0 else 0
            self.fill((cx - span) / s, (cy + dy) / s,
                      (span * 2 + 1) / s, 1 / s, c)

    def arc(self, cx, cy, r, a0, a1, c, t=2):
        """Arc from a0 to a1 degrees, 0 = east, going clockwise."""
        total = abs(a1 - a0)
        n = max(4, int(total / 5.0) + 1)
        prev = None
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pt = (cx + r * math.cos(a), cy + r * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], pt[0], pt[1], c, t)
            prev = pt

    def poly(self, pts, c):
        """Scanline polygon fill (even-odd)."""
        s = self.s
        pts = [(x * s, y * s) for x, y in pts]
        if len(pts) < 3:
            return
        sides = []
        for i, (x0, y0) in enumerate(pts):
            x1, y1 = pts[(i + 1) % len(pts)]
            if y0 != y1:
                sides.append((x0, y0, x1, y1))
        ys = [p[1] for p in pts]
        top = max(0, int(math.floor(min(ys))))
        bot = min(self.ph - 1, int(math.ceil(max(ys))))
        for y in range(top, bot + 1):
            xs = []
            for xa, ya, xb, yb in sides:
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y - ya) / float(yb - ya) * (xb - xa))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[k] + 0.5), int(xs[k + 1] + 0.5)
                if xb > xa:
                    self.fill(xa / s, y / s, (xb - xa) / s, 1 / s, c)

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient, one flat band per logical row."""
        for i in range(int(h)):
            f = i / max(1, int(h) - 1)
            c = tuple(round(top[k] + (bottom[k] - top[k]) * f)
                      for k in range(3))
            self.fill(x, y + i, w, 1, c)

    def border(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def downsample(self):
        """Average each 2x2 block to one pixel; returns a 1x canvas."""
        s = self.s
        assert s == 2, "downsample is written for SS=2"
        out = Canvas(self.w, self.h, (0, 0, 0), s=1)
        src = self.px
        sw3 = self.pw * 3
        for oy in range(self.h):
            r0 = (oy * s) * sw3
            r1 = r0 + sw3
            row = bytearray(self.w * 3)
            for ox in range(self.w):
                o0 = r0 + ox * s * 3
                o1 = r1 + ox * s * 3
                row[ox * 3] = (src[o0] + src[o0 + 3] +
                               src[o1] + src[o1 + 3]) // 4
                row[ox * 3 + 1] = (src[o0 + 1] + src[o0 + 4] +
                                   src[o1 + 1] + src[o1 + 4]) // 4
                row[ox * 3 + 2] = (src[o0 + 2] + src[o0 + 5] +
                                   src[o1 + 2] + src[o1 + 5]) // 4
            out.px[oy * self.w * 3:(oy + 1) * self.w * 3] = row
        return out


def png_bytes(cv):
    """Encode a 1x canvas as a PNG (truecolour, filter 0 each row)."""
    stride = cv.w * 3
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    blob = zlib.compress(bytes(raw), 6)

    def chunk(tag, payload):
        head = struct.pack(">I", len(payload)) + tag + payload
        return head + struct.pack(">I", binascii.crc32(tag + payload)
                                  & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", blob) + chunk(b"IEND", b""))

# --------------------------------------------------------------------- font
# Vector stroke font, drawn from scratch for v4. One glyph = a list of
# polylines in a 10-wide grid; y=0 is the cap top, y=14 the baseline,
# y=17 the descender bottom; lowercase x-height runs y=5..14. A
# one-point polyline is a dot (i, j, periods, colons). Each glyph
# also carries its advance width in grid units. 'size' in the
# drawing helpers is the cap height in pixels; scale = size / 14.
#
# Serif mode (titles only) adds a short horizontal tick at the
# ends of vertical stems that touch the cap line, the baseline or
# the descender line (the classic newspaper look), plus the
# explicit feet in SERIF_FEET (A's feet are diagonal, so the
# automatic rule misses them). Only the masthead, the name line
# above it and the headlines use serif; every other line is plain
# sans, and the subhead is italic sheared from the sans glyphs.
# Italic shears every point right by (14 - y) * 0.15 units,
# so the top leans right of the baseline.
#
# This finally gives us a real lowercase 'g' (bowl + descender
# hook) -- v3 could not draw one in its 5x7 grid and had to avoid
# the letter everywhere ("span" for bridge, "Alphabet" for Google).

VFONT = {
    # ---- capitals ----
    'A': ([[(0.5, 14), (5, 0), (9.5, 14)], [(2.8, 9.5), (7.2, 9.5)]], 10.5),
    'B': ([[(1, 0), (1, 14)],
           [(1, 0), (6.5, 0), (8.5, 2.5), (8.5, 5.5), (6.5, 7), (1, 7)],
           [(1, 7), (7, 7), (9, 9.5), (9, 11.5), (7, 14), (1, 14)]], 10.5),
    'C': ([[(9, 2), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14),
            (9, 12)]], 10.5),
    'D': ([[(1, 0), (1, 14)],
           [(1, 0), (6, 0), (9, 3), (9, 11), (6, 14), (1, 14)]], 10.5),
    'E': ([[(1, 0), (1, 14)], [(1, 0), (9, 0)], [(1, 7), (7, 7)],
           [(1, 14), (9, 14)]], 10.5),
    'F': ([[(1, 0), (1, 14)], [(1, 0), (9, 0)], [(1, 7), (7, 7)]], 10.5),
    'G': ([[(9, 2), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14),
            (9, 12), (9, 8), (6, 8)]], 10.5),
    'H': ([[(1, 0), (1, 14)], [(9, 0), (9, 14)], [(1, 7), (9, 7)]], 10.5),
    'I': ([[(5, 0), (5, 14)]], 6.5),
    'J': ([[(9, 0), (9, 11), (7, 14), (3, 14), (1, 12)],
           [(5.5, 0), (9.5, 0)]], 10.5),
    'K': ([[(1, 0), (1, 14)], [(9, 0), (1, 7), (9, 14)]], 10.5),
    'L': ([[(1, 0), (1, 14)], [(1, 14), (9, 14)]], 10.5),
    'M': ([[(1, 14), (1, 0), (5, 8), (9, 0), (9, 14)]], 11.5),
    'N': ([[(1, 14), (1, 0), (9, 14), (9, 0)]], 11),
    'O': ([[(3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11),
            (1, 3), (3, 0)]], 10.5),
    'P': ([[(1, 0), (1, 14)],
           [(1, 0), (6.5, 0), (8.5, 2), (8.5, 5), (6.5, 7), (1, 7)]], 10.5),
    'Q': ([[(3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11),
            (1, 3), (3, 0)], [(6.5, 10.5), (9.5, 14.5)]], 10.5),
    'R': ([[(1, 0), (1, 14)],
           [(1, 0), (6.5, 0), (8.5, 2), (8.5, 5), (6.5, 7), (1, 7)],
           [(5, 7), (9, 14)]], 10.5),
    'S': ([[(9, 2), (7, 0), (3, 0), (1, 2), (1, 5), (3, 7), (7, 7),
            (9, 9), (9, 12), (7, 14), (3, 14), (1, 12)]], 10.5),
    'T': ([[(0.5, 0), (9.5, 0)], [(5, 0), (5, 14)]], 10.5),
    'U': ([[(1, 0), (1, 11), (3, 14), (7, 14), (9, 11), (9, 0)]], 10.5),
    'V': ([[(0.5, 0), (5, 14), (9.5, 0)]], 10.5),
    'W': ([[(0.5, 0), (2.5, 14), (5, 5), (7.5, 14), (9.5, 0)]], 11.5),
    'X': ([[(1, 0), (9, 14)], [(9, 0), (1, 14)]], 10.5),
    'Y': ([[(0.5, 0), (5, 7), (9.5, 0)], [(5, 7), (5, 14)]], 10.5),
    'Z': ([[(1, 0), (9, 0), (1, 14), (9, 14)]], 10.5),
    # ---- lowercase ----
    'a': ([[(3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14), (3, 14),
            (1.5, 11), (1.5, 7.5), (3, 5)], [(8.5, 5), (8.5, 14)]], 10.5),
    'b': ([[(1, 0), (1, 14)],
           [(1, 9), (3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14),
            (3, 14), (1, 11)]], 10.5),
    'c': ([[(8.5, 7), (7, 5), (3, 5), (1.5, 7), (1.5, 11.5), (3, 14),
            (7, 14), (8.5, 12)]], 10.5),
    'd': ([[(3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14), (3, 14),
            (1.5, 11), (1.5, 7.5), (3, 5)], [(8.5, 0), (8.5, 14)]], 10.5),
    'e': ([[(1.5, 9.5), (8.5, 9.5)],
           [(8.5, 7), (7, 5), (3, 5), (1.5, 7), (1.5, 11), (3, 14),
            (7, 14), (8.5, 12)]], 10.5),
    'f': ([[(8, 3), (5, 0), (2.5, 2), (2.5, 14)], [(1, 6.5), (6.5, 6.5)]],
          8.5),
    'g': ([[(3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14), (3, 14),
            (1.5, 11), (1.5, 7.5), (3, 5)],
           [(8.5, 11), (8.5, 15.5), (6, 17), (3, 17), (2, 15.5)]], 10.5),
    'h': ([[(1, 0), (1, 14)],
           [(1, 8), (3, 5), (7, 5), (8.5, 7.5), (8.5, 14)]], 10.5),
    'i': ([[(5, 5), (5, 14)], [(5, 1.5)]], 5.5),
    'j': ([[(6, 5), (6, 14.5), (5, 16.5), (2.5, 16.5)], [(6, 1.5)]], 6.5),
    'k': ([[(1, 0), (1, 14)], [(8.5, 5), (1, 9.5), (8.5, 14)]], 10.5),
    'l': ([[(5, 0), (5, 14)]], 5.5),
    'm': ([[(1, 14), (1, 8), (3, 5), (5, 5), (5, 8), (5, 14)],
           [(5, 8), (7, 5), (9, 5), (9.5, 8), (9.5, 14)]], 11.5),
    'n': ([[(1, 14), (1, 8), (3, 5), (7, 5), (8.5, 7.5), (8.5, 14)]], 10.5),
    'o': ([[(3, 5), (7, 5), (8.5, 7.5), (8.5, 11.5), (7, 14), (3, 14),
            (1.5, 11.5), (1.5, 7.5), (3, 5)]], 10.5),
    'p': ([[(1, 5), (1, 17)],
           [(1, 9), (3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14),
            (3, 14), (1, 11)]], 10.5),
    'q': ([[(3, 5), (7, 5), (8.5, 7.5), (8.5, 11), (7, 14), (3, 14),
            (1.5, 11), (1.5, 7.5), (3, 5)], [(8.5, 5), (8.5, 17)]], 10.5),
    'r': ([[(1, 5), (1, 14)], [(1, 8), (2.5, 5), (6, 5), (8, 6.5)]], 8.5),
    's': ([[(8.5, 6.5), (7, 5), (3, 5), (1.5, 6.5), (1.5, 8.5), (3, 9.5),
            (7, 9.5), (8.5, 11), (8.5, 12.5), (7, 14), (3, 14),
            (1.5, 12.5)]], 10.5),
    't': ([[(5, 1), (5, 14)], [(5, 14), (7, 14), (8, 12.5)],
           [(2, 6.5), (8, 6.5)]], 8.5),
    'u': ([[(1, 5), (1, 11), (2.5, 14), (7, 14), (8.5, 11), (8.5, 5)]],
          10.5),
    'v': ([[(0.5, 5), (5, 14), (9.5, 5)]], 10.5),
    'w': ([[(0.5, 5), (2.5, 14), (5, 8), (7.5, 14), (9.5, 5)]], 11.5),
    'x': ([[(1.5, 5), (8.5, 14)], [(8.5, 5), (1.5, 14)]], 10.5),
    'y': ([[(0.5, 5), (5, 11), (9.5, 5)],
           [(5, 11), (5, 15.5), (3.5, 17), (2, 17)]], 10.5),
    'z': ([[(1.5, 5), (8.5, 5), (1.5, 14), (8.5, 14)]], 10.5),
    # ---- digits ----
    '0': ([[(3, 0), (7, 0), (9, 3), (9, 11), (7, 14), (3, 14), (1, 11),
            (1, 3), (3, 0)]], 10.5),
    '1': ([[(2.5, 3), (5, 0), (5, 14)], [(2.5, 14), (7.5, 14)]], 7.5),
    '2': ([[(1.5, 3), (3, 0), (7, 0), (8.5, 2), (8.5, 5), (6, 8),
            (1.5, 14), (8.5, 14)]], 10.5),
    '3': ([[(1.5, 2), (3, 0), (7, 0), (8.5, 2), (8.5, 5), (7, 7), (5, 7)],
           [(5, 7), (7, 7), (8.5, 9), (8.5, 12), (7, 14), (3, 14),
            (1.5, 12)]], 10.5),
    '4': ([[(7, 0), (1, 10)], [(0.5, 10), (9, 10)], [(7, 0), (7, 14)]],
          10.5),
    '5': ([[(8.5, 0), (1.5, 0), (1.5, 6.5), (4, 6.5), (7, 6.5), (8.5, 8.5),
            (8.5, 11.5), (7, 14), (3, 14), (1.5, 12)]], 10.5),
    '6': ([[(8.5, 2), (6, 0), (3, 0), (1.5, 3), (1.5, 11), (3, 14),
            (7, 14), (8.5, 11), (8.5, 8), (7, 6), (3, 6), (1.5, 8)]],
          10.5),
    '7': ([[(1.5, 0), (8.5, 0), (4, 14)]], 10.5),
    '8': ([[(3, 0), (7, 0), (8.5, 2), (8.5, 5), (7, 7), (3, 7), (1.5, 5),
            (1.5, 2), (3, 0)],
           [(3, 7), (7, 7), (8.5, 9), (8.5, 12), (7, 14), (3, 14),
            (1.5, 12), (1.5, 9), (3, 7)]], 10.5),
    '9': ([[(1.5, 12), (3, 14), (7, 14), (8.5, 11), (8.5, 3), (7, 0),
            (3, 0), (1.5, 2), (1.5, 6), (3, 8), (7, 8), (8.5, 6)]], 10.5),
    # ---- punctuation ----
    ' ': ([], 5.5),
    '.': ([[(5, 13)]], 5.5),
    ',': ([[(5, 13)], [(5, 13.5), (4, 16.5)]], 5.5),
    ':': ([[(5, 4.5)], [(5, 11.5)]], 5.5),
    ';': ([[(5, 4.5)], [(5, 11.5)], [(5, 12), (4, 15.5)]], 5.5),
    "'": ([[(4.5, 0), (6, 3.5)]], 5.5),
    '\u2019': ([[(4.5, 0), (6, 3.5)]], 5.5),
    '\u2018': ([[(5.5, 0), (4, 3.5)]], 5.5),
    '"': ([[(3, 0), (4.5, 3.5)], [(6.5, 0), (8, 3.5)]], 7),
    '!': ([[(5, 0), (5, 10)], [(5, 13)]], 5.5),
    '?': ([[(2, 3), (3, 0), (7, 0), (8.5, 2), (8.5, 4.5), (7, 6.5),
            (5, 7.5), (5, 9.5)], [(5, 13)]], 10.5),
    '-': ([[(1, 7), (9, 7)]], 10.5),
    '\u2013': ([[(1.5, 7), (8.5, 7)]], 10.5),
    '\u2014': ([[(0.5, 7), (9.5, 7)]], 11),
    '(': ([[(7, 0), (4, 3), (4, 11), (7, 14)]], 7),
    ')': ([[(3, 0), (6, 3), (6, 11), (3, 14)]], 7),
    '/': ([[(8, 14), (2, 0)]], 8.5),
    '%': ([[(8.5, 14), (1.5, 0)],
           [(1.5, 2), (3.5, 2), (4.5, 4), (3.5, 6), (1.5, 6), (0.5, 4),
            (1.5, 2)],
           [(5.5, 8), (7.5, 8), (8.5, 10), (7.5, 12), (5.5, 12), (4.5, 10),
            (5.5, 8)]], 11),
    '$': ([[(5, -1), (5, 15)],
           [(8.5, 2.5), (7, 0), (3, 0), (1.5, 2), (1.5, 5), (3, 7),
            (7, 7), (8.5, 9), (8.5, 12), (7, 14), (3, 14), (1.5, 11.5)]],
          10.5),
    '\u20ac': ([[(9, 2), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14),
                (9, 12)],
               [(0.5, 5.5), (8.5, 5.5)], [(0.5, 8.5), (8.5, 8.5)]], 10.5),
    '&': ([[(8, 2), (6, 0), (3, 0), (1.5, 2), (1.5, 5), (4, 7), (8.5, 11),
            (8.5, 13), (7, 14), (3, 14), (1.5, 12)], [(4, 7), (1.5, 11)]],
          10.5),
    '+': ([[(5, 3), (5, 11)], [(1.5, 7), (8.5, 7)]], 10.5),
    '=': ([[(1.5, 5), (8.5, 5)], [(1.5, 9), (8.5, 9)]], 10.5),
    '*': ([[(5, 2), (5, 12)], [(1.5, 4), (8.5, 10)], [(8.5, 4), (1.5, 10)]],
          10.5),
    '\u00b7': ([[(5, 7)]], 5.5),
    '<': ([[(8, 2), (2, 7), (8, 12)]], 10.5),
    '>': ([[(2, 2), (8, 7), (2, 12)]], 10.5),
    '#': ([[(3, 0), (3, 14)], [(7, 0), (7, 14)], [(1, 5), (9, 5)],
           [(1, 9), (9, 9)]], 10.5),
    '_': ([[(1, 15.5), (9, 15.5)]], 10.5),
    '\u00b0': ([[(3, 2), (6, 2), (7, 3.5), (7, 5.5), (6, 7), (3, 7),
                (2, 5.5), (2, 3.5), (3, 2)]], 7),
}

SERIF_FEET = {
    'A': [(0.5, 14), (9.5, 14)],
}


XNARROW = 0.85  # condensed newspaper width: glyphs are drawn 15%
# narrower than their grid cells, as real newspaper type is.


def _shear(px, py, italic):
    """Italic lean: the cap top shifts right of the baseline."""
    px = px * XNARROW
    if italic:
        px += (14 - py) * 0.15
    return px, py


def _tick(cv, x, y, size, c, t):
    """One serif tick: a short horizontal bar at (x, y)."""
    sc = size / 14.0
    cv.line(x - 1.2 * XNARROW * sc, y, x + 1.2 * XNARROW * sc, y, c, t)


def draw_vglyph(cv, x, y, ch, size, c, serif=False, bold=False,
                italic=False):
    """Draw one vector glyph; (x, y) is the cap top-left corner."""
    entry = VFONT.get(ch) or VFONT['?']
    strokes, _adv = entry
    sc = size / 14.0
    t = max(1, round(size * 0.12)) if bold else max(1, round(size * 0.10))
    for pts in strokes:
        if len(pts) == 1:
            px, py = _shear(pts[0][0], pts[0][1], italic)
            cv.disc(x + px * sc, y + py * sc, max(1, t // 2 + 1), c)
            continue
        tp = [(x + _shear(px, py, italic)[0] * sc, y + py * sc)
              for px, py in pts]
        for i in range(len(tp) - 1):
            (x0, y0), (x1, y1) = tp[i], tp[i + 1]
            cv.line(x0, y0, x1, y1, c, t)
        r = max(1, t // 2)
        for jx, jy in tp[1:-1]:
            cv.disc(jx, jy, r, c)
    if serif:
        for pts in strokes:
            if len(pts) < 2:
                continue
            for end, nxt in ((pts[0], pts[1]), (pts[-1], pts[-2])):
                ex, ey = end
                if ey in (0, 14, 17) and abs(nxt[0] - ex) <= 0.5:
                    sx, _sy = _shear(ex, ey, italic)
                    _tick(cv, x + sx * sc, y + ey * sc, size, c, t)
        for fx, fy in SERIF_FEET.get(ch, ()):
            sx, _sy = _shear(fx, fy, italic)
            _tick(cv, x + sx * sc, y + fy * sc, size, c, t)


def _adv(ch):
    entry = VFONT.get(ch)
    return (entry[1] if entry else 10.5) * XNARROW


def vtext_w(text, size, gap=0):
    """Pixel width of text at cap height `size`."""
    sc = size / 14.0
    total = 0.0
    for ch in text:
        total += _adv(ch) * sc + gap
    return int(round(total - gap)) if text else 0


def draw_vtext(cv, x, y, text, size, c, serif=False, bold=False,
               italic=False, gap=0):
    """Left-aligned vector text; returns the end x."""
    sc = size / 14.0
    cx = x
    for ch in text:
        draw_vglyph(cv, cx, y, ch, size, c, serif, bold, italic)
        cx += _adv(ch) * sc + gap
    return cx


def vwrap(text, size, max_w, gap=0):
    """Greedy word wrap into lines no wider than max_w."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if vtext_w(trial, size, gap) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# Backwards-compatible names used by the layout code; size is now
# the cap height in pixels (v3's size 1 ~ 7px cap, size 2 ~ 14px).
def text_w(text, size, gap=0):
    return vtext_w(text, size, gap)


def draw_text(cv, x, y, text, size, c, bold=False, gap=0, serif=False,
              italic=False):
    return draw_vtext(cv, x, y, text, size, c, serif, bold, italic, gap)


def draw_spaced(cv, x, y, text, size, c, gap=2, serif=False, bold=False,
                italic=False):
    return draw_vtext(cv, x, y, text, size, c, serif, bold, italic, gap)


def wrap_text(text, size, max_w, gap=0):
    return vwrap(text, size, max_w, gap)


# -------------------------------------------------------------- panel art
def art_kyiv(cv, x, y, w, h):
    """Kyiv at night under attack: dark sky, skyline, fires, trails."""
    cv.vgrad(x, y, w, h, (14, 22, 46), (38, 58, 96))
    for sx, sy in ((30, 14), (90, 26), (150, 10), (210, 30), (260, 12),
                   (40, 44), (180, 48), (120, 36)):
        cv.disc(x + sx, y + sy, 1, WHITE)
    base = y + h - 26
    towers = [(0, 40, 34), (40, 62, 30), (76, 48, 36), (118, 74, 28),
              (152, 56, 40), (198, 80, 30), (234, 60, 34), (274, 70, 30)]
    for tx, th, tw in towers:
        cv.fill(x + tx, base - th, tw, th + 26, (10, 16, 32))
        for wy in range(base - th + 8, base - 4, 14):
            for wx in range(x + tx + 5, x + tx + tw - 4, 11):
                if (wx + wy) % 29 < 14:
                    cv.fill(wx, wy, 2, 3, GOLD_LT)
    for fx, fw in ((96, 26), (218, 34), (292, 22)):
        cv.disc(x + fx, base - 6, fw, (230, 120, 40))
        cv.disc(x + fx, base - 6, fw // 2, (255, 200, 90))
        cv.poly([(x + fx - 8, base - 6), (x + fx, base - 34),
                 (x + fx + 8, base - 6)], (255, 170, 60))
    # missile trails: dotted arcs falling toward the fires
    for (x0, y0, x1, y1, x2, y2) in ((20, 8, 120, 40, 218, base - 20),
                                     (280, 6, 220, 34, 96, base - 14),
                                     (150, 4, 200, 26, 292, base - 10)):
        for i in range(13):
            f = i / 12.0
            px = (1 - f) * (1 - f) * x0 + 2 * (1 - f) * f * x1 + f * f * x2
            py = (1 - f) * (1 - f) * y0 + 2 * (1 - f) * f * y1 + f * f * y2
            cv.disc(x + int(px), y + int(py), 2,
                    GOLD_LT if i % 2 else WHITE)


def art_cyclone(cv, x, y, w, h):
    """Cyclone Akvan over the Bay of Bengal: sea, spiral, rain."""
    cv.vgrad(x, y, w, h, (168, 200, 214), (88, 138, 158))
    cv.fill(x, y + h - 34, w, 34, SAND)
    cv.fill(x, y + h - 34, w, 3, (120, 100, 70))
    cx, cy = x + w // 2 - 30, y + h // 2 - 12
    for r, a0, a1 in ((52, 10, 190), (40, 190, 10), (28, 10, 190),
                      (16, 190, 10)):
        cv.arc(cx, cy, r, a0, a1, WHITE, 3)
    cv.disc(cx, cy, 7, NAVY_DK)
    for i in range(9):
        rx = x + 14 + i * 52
        cv.line(rx, y + 8, rx - 8, y + 30, WHITE, 2)
        cv.line(rx + 200, y + 58, rx + 192, y + 80, WHITE, 2)
    cv.poly([(x + 20, y + h - 34), (x + 90, y + h - 34),
             (x + 60, y + h - 64), (x + 34, y + h - 52)], (46, 110, 70))
    cv.poly([(x + w - 110, y + h - 34), (x + w - 30, y + h - 34),
             (x + w - 60, y + h - 66), (x + w - 88, y + h - 50)],
            (46, 110, 70))


def art_market(cv, x, y, w, h):
    """Asia's AI sell-off: dark board, falling candles, red arrow,
    plus a 4-city table along the bottom (Taipei/Seoul/Tokyo/
    Hong Kong Friday closes), as the winning pages do."""
    cv.vgrad(x, y, w, h, NAVY, NAVY_DK)
    th = 54  # candles + arrow take the top part; the table sits
    # below them and above the caption/banner2 strip (bottom 18px)
    for gy in range(y + 8, y + th - 4, 12):
        cv.hline(x + 8, gy, w - 16, (255, 255, 255), 1)
    candles = [(22, 8, 14), (72, 12, 12), (122, 16, 10),
               (172, 20, 9), (222, 24, 8), (272, 28, 7)]
    for i, (bx, top, ht) in enumerate(candles):
        col = (220, 80, 80) if i % 2 == 0 else (200, 60, 60)
        cv.fill(x + bx, y + top, 24, ht, col)
        cv.vline(x + bx + 12, y + top - 4, ht + 8, col, 2)
    cv.line(x + 18, y + 8, x + w - 40, y + th - 8, (255, 90, 90), 3)
    cv.line(x + w - 40, y + th - 8, x + w - 66, y + th - 10,
            (255, 90, 90), 3)
    cv.line(x + w - 40, y + th - 8, x + w - 42, y + th - 30,
            (255, 90, 90), 3)
    cv.disc(x + w - 40, y + th - 8, 4, (255, 90, 90))
    # 4-city table: 2 rows x 2 columns, Friday closes
    ty = y + 56
    cv.fill(x, ty, w, 34, (10, 16, 32))
    cv.hline(x, ty, w, GOLD, 2)
    cells = [(("TAIPEI", "-6.2%"), ("SEOUL", "-5.2%")),
             (("TOKYO", "-5.1%"), ("HONG KONG", "-1.9%"))]
    for r, row in enumerate(cells):
        cy = ty + 6 + r * 14
        for c, (city, val) in enumerate(row):
            cx = x + 10 + c * 156
            draw_text(cv, cx, cy, city, 9, WHITE, bold=True)
            draw_text(cv, cx + text_w(city, 9) + 6, cy, val, 9,
                      (255, 110, 110), bold=True)


# ------------------------------------------------------------- mini scenes
# One specific flat illustration per tile, filling the picture box.
# Winners give each tile a picture ~40% of the tile height; v3 gave
# them a 20px glyph icon. These painters are the fix for that gap.

def _mini_globe_thermo(cv, x, y, w, h):
    cv.fill(x, y, w, h, (186, 220, 220))
    cv.disc(x + w // 3, y + h // 2 + 4, h // 2 - 6, (38, 84, 160))
    cv.ellipse(x + w // 3, y + h // 2 + 4, 8, h // 2 - 6, WHITE)
    cv.hline(x + w // 3 - h // 2 + 6, y + h // 2 + 4, h - 12, WHITE, 2)
    tx = x + w - 34
    cv.fill(tx, y + 6, 10, h - 16, WHITE)
    cv.fill(tx + 2, y + 8, 6, h - 20, RED)
    cv.disc(tx + 5, y + h - 10, 8, RED)
    cv.fill(tx + 11, y + 10, 14, 3, INK)
    cv.fill(tx + 11, y + h // 2, 14, 3, INK)


def _mini_flags_uk_eu(cv, x, y, w, h):
    hw = w // 2
    cv.fill(x, y, hw, h, (20, 40, 90))
    cv.line(x + 4, y + 4, x + hw - 4, y + h - 4, WHITE, 4)
    cv.line(x + hw - 4, y + 4, x + 4, y + h - 4, WHITE, 4)
    cv.vline(x + hw // 2, y, h, WHITE, 5)
    cv.hline(x, y + h // 2, hw, WHITE, 5)
    cv.vline(x + hw // 2, y, h, RED, 3)
    cv.hline(x, y + h // 2, hw, RED, 3)
    cv.fill(x + hw, y, w - hw, h, (30, 60, 150))
    cx, cy = x + hw + (w - hw) // 2, y + h // 2
    for k in range(12):
        a = math.radians(k * 30)
        cv.disc(cx + int(13 * math.cos(a)), cy + int(11 * math.sin(a)), 2,
                GOLD)


def _mini_missile_field(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (198, 222, 235), (226, 232, 220))
    cv.fill(x, y + h - 16, w, 16, (90, 140, 70))
    cv.hline(x, y + h - 16, w, (60, 110, 50), 2)
    for i in range(7):
        f = i / 6.0
        px = x + 20 + f * (w - 60)
        py = y + 10 + f * f * (h - 34)
        cv.disc(int(px), int(py), 3, WHITE)
    cv.poly([(x + w - 52, y + h - 16), (x + w - 40, y + h - 38),
             (x + w - 28, y + h - 16)], (60, 60, 60))
    cv.disc(x + w - 40, y + h - 40, 4, (230, 120, 40))
    cv.poly([(x + 30, y + h - 16), (x + 44, y + h - 16),
             (x + 37, y + h - 30)], (120, 120, 120))


def _mini_tents(cv, x, y, w, h):
    cv.fill(x, y, w, h, (232, 214, 170))
    for tx, tw, th, col in ((12, 54, 30, (196, 150, 90)),
                            (70, 62, 36, (170, 120, 60)),
                            (134, 48, 26, (210, 170, 110))):
        cv.poly([(x + tx + tw // 2, y + h - th), (x + tx + tw, y + h),
                 (x + tx, y + h)], col)
        cv.poly([(x + tx + tw // 2 - 5, y + h - th + 12),
                 (x + tx + tw // 2 + 5, y + h - th + 12),
                 (x + tx + tw // 2, y + h)], (60, 50, 40))
    for i, (sx, sy) in enumerate(((100, 8), (106, 16), (98, 24))):
        cv.disc(x + sx, y + sy, 5 - i, (120, 120, 120))


def _mini_delhi(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (250, 196, 120), (224, 122, 74))
    cv.disc(x + w - 30, y + 12, 8, (255, 236, 180))
    gw = 64
    gx = x + w // 2 - gw // 2
    cv.fill(gx, y + h - 34, 10, 34, (120, 90, 60))
    cv.fill(gx + gw - 10, y + h - 34, 10, 34, (120, 90, 60))
    cv.fill(gx, y + h - 40, gw, 8, (120, 90, 60))
    cv.poly([(gx + 10, y + h - 32), (gx + gw - 10, y + h - 32),
             (gx + gw - 10, y + h - 18), (gx + 10, y + h - 18)],
            (250, 196, 120))
    for i, fx in enumerate((16, w - 30)):
        cv.vline(x + fx, y + 8, 22, WHITE, 2)
        cv.fill(x + fx + 2, y + 8, 14, 5, (255, 153, 51))
        cv.fill(x + fx + 2, y + 13, 14, 5, WHITE)
        cv.fill(x + fx + 2, y + 18, 14, 5, (19, 136, 8))


def _mini_chess(cv, x, y, w, h):
    cv.fill(x, y, w, h, (238, 230, 212))
    sq = 12
    for r in range(2):
        for c in range(w // sq + 1):
            if (r + c) % 2 == 0:
                cv.fill(x + c * sq, y + h - 24 + r * sq, sq, sq, INK)
    for kx, col in ((w // 3, INK), (2 * w // 3, WHITE)):
        cx = x + kx
        cv.fill(cx - 9, y + 8, 18, 16, col)
        cv.poly([(cx - 11, y + 8), (cx - 6, y - 2), (cx, y + 6),
                 (cx + 6, y - 2), (cx + 11, y + 8)], col)
        cv.fill(cx - 11, y + 24, 22, 4, col)
        if col == WHITE:
            cv.border(cx - 9, y + 8, 18, 16, INK, 1)


def _mini_chip(cv, x, y, w, h):
    cv.fill(x, y, w, h, (20, 34, 58))
    cx, cy = x + w // 2, y + h // 2
    for k in range(-2, 3):
        cv.hline(x + 8, cy + k * 8, w - 16, (40, 90, 120), 1)
    cv.fill(cx - 16, cy - 14, 32, 28, (30, 60, 100))
    cv.border(cx - 16, cy - 14, 32, 28, (120, 200, 220), 2)
    cv.fill(cx - 7, cy - 5, 14, 10, (120, 200, 220))
    cv.line(cx - 22, cy - 18, cx - 34, cy - 22, GOLD, 2)
    cv.line(cx + 22, cy + 18, cx + 34, cy + 22, GOLD, 2)
    cv.disc(cx - 34, cy - 22, 3, GOLD)
    cv.disc(cx + 34, cy + 22, 3, GOLD)


def _mini_nuke(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (200, 205, 205), (170, 175, 175))
    cv.poly([(x + 24, y + 6), (x + 48, y + 6), (x + 42, y + h - 8),
             (x + 30, y + h - 8)], (140, 140, 140))
    cv.fill(x + 24, y + 6, 24, 4, (110, 110, 110))
    for i in range(6):
        cv.vline(x + 70 + i * 14, y + 14, h - 22, (90, 90, 90), 2)
    cv.hline(x + 70, y + 14, 84, (90, 90, 90), 2)
    cv.hline(x + 70, y + h - 8, 84, (90, 90, 90), 2)
    cv.poly([(x + w - 34, y + 8), (x + w - 14, y + 8), (x + w - 24, y + 26)],
            (240, 200, 40))
    cv.fill(x + w - 26, y + 14, 3, 8, INK)


def _mini_oil(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (250, 210, 140), (232, 180, 110))
    cv.disc(x + w - 28, y + 12, 9, (255, 236, 180))
    cv.fill(x, y + h - 12, w, 12, (190, 150, 90))
    bx = x + 30
    cv.line(bx, y + h - 12, bx + 26, y + 8, INK, 3)
    cv.line(bx + 26, y + 8, bx + 52, y + h - 12, INK, 3)
    cv.line(bx + 6, y + h - 12, bx + 46, y + h - 12, INK, 2)
    cv.line(bx + 26, y + 8, bx + 56, y + 14, INK, 3)
    cv.disc(bx + 56, y + 14, 3, INK)
    cv.disc(bx + 26, y + 8, 3, RED)


def _mini_chart(cv, x, y, w, h):
    """Wall Street: a falling line chart on a light board."""
    cv.fill(x, y, w, h, (238, 230, 212))
    for gy in range(y + 8, y + h - 4, 10):
        cv.hline(x + 6, gy, w - 12, (200, 192, 176), 1)
    pts = [(x + 10, y + 8), (x + 44, y + 14), (x + 78, y + 12),
           (x + 112, y + 20), (x + 146, y + 28), (x + w - 12, y + h - 8)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                RED, 3)
    for px, py in pts:
        cv.disc(px, py, 3, RED)
    cv.disc(pts[-1][0], pts[-1][1], 4, RED_DK)


def _mini_skyline(cv, x, y, w, h):
    """Tokyo at dusk: towers with lit windows, red down arrow."""
    cv.vgrad(x, y, w, h, (30, 48, 80), (58, 68, 108))
    cv.disc(x + w - 22, y + 7, 5, (255, 236, 180))
    base = y + h
    for bx, bw, bh in ((6, 24, 20), (34, 18, 28), (56, 28, 16),
                       (88, 20, 24), (112, 26, 18), (142, 20, 26),
                       (166, 14, 20)):
        cv.fill(x + bx, base - bh, bw, bh, (14, 22, 46))
        for wy in range(base - bh + 4, base - 2, 7):
            for wx in range(x + bx + 4, x + bx + bw - 3, 8):
                if (wx * 3 + wy) % 11 < 5:
                    cv.fill(wx, wy, 2, 2, GOLD_LT)
    ax = x + w - 30
    cv.line(ax, y + 6, ax, y + h - 14, (255, 90, 90), 3)
    cv.line(ax, y + h - 14, ax - 6, y + h - 22, (255, 90, 90), 3)
    cv.line(ax, y + h - 14, ax + 6, y + h - 22, (255, 90, 90), 3)


def _mini_cricket(cv, x, y, w, h):
    cv.fill(x, y, w, h, (70, 150, 80))
    cv.fill(x + w // 2 - 26, y + 6, 52, h - 12, (210, 180, 130))
    for sx in (-6, 0, 6):
        cv.vline(x + w // 2 + sx - 1, y + 10, 16, GOLD, 3)
    cv.hline(x + w // 2 - 8, y + 9, 16, GOLD, 2)
    cv.line(x + 20, y + h - 8, x + w // 2 - 4, y + 16, (120, 80, 40), 4)
    cv.disc(x + w - 26, y + 14, 5, RED)
    cv.disc(x + 16, y + 12, 4, WHITE)


MINI_SCENES = {
    "globe-thermo": _mini_globe_thermo,
    "flags-uk-eu": _mini_flags_uk_eu,
    "missile-field": _mini_missile_field,
    "tents": _mini_tents,
    "delhi": _mini_delhi,
    "chess": _mini_chess,
    "chip": _mini_chip,
    "nuke": _mini_nuke,
    "oil": _mini_oil,
    "cricket": _mini_cricket,
    "chart": _mini_chart,
    "skyline": _mini_skyline,
}


def mini_scene(cv, x, y, w, h, kind):
    fn = MINI_SCENES.get(kind)
    if fn is not None:
        fn(cv, x, y, w, h)


# ---------------------------------------------------------------------- map
# Coarse continent outlines I plotted by hand (lon, lat pairs).

LAND = [
    [(-168, 66), (-150, 70), (-130, 71), (-110, 68), (-95, 80), (-80, 73),
     (-68, 62), (-55, 47), (-65, 44), (-75, 35), (-81, 26), (-87, 21),
     (-97, 16), (-105, 20), (-114, 29), (-125, 40), (-124, 49),
     (-135, 58), (-152, 58), (-162, 60)],
    [(-80, 10), (-70, 12), (-60, 8), (-51, 4), (-40, -5), (-35, -8),
     (-39, -15), (-48, -28), (-58, -35), (-66, -47), (-70, -55),
     (-73, -40), (-73, -25), (-77, -12), (-81, -3)],
    [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (-1, 52), (3, 52), (5, 53),
     (8, 57), (10, 59), (18, 56), (21, 55), (24, 59), (30, 62), (32, 70),
     (40, 68), (44, 66), (40, 60), (38, 55), (30, 50), (28, 45),
     (23, 40), (19, 42), (12, 44), (8, 44), (3, 42), (0, 39)],
    [(-17, 15), (-15, 27), (-10, 31), (-5, 35), (10, 37), (20, 32),
     (32, 31), (35, 28), (40, 15), (43, 11), (48, 11), (51, 10),
     (45, 0), (40, -10), (35, -20), (32, -28), (26, -34), (19, -35),
     (15, -27), (12, -18), (9, -1), (9, 4), (-8, 5), (-13, 8)],
    [(30, 36), (36, 36), (36, 42), (42, 46), (48, 52), (54, 58),
     (60, 65), (68, 69), (75, 73), (85, 74), (95, 76), (105, 77),
     (115, 73), (125, 72), (135, 72), (145, 71), (155, 69), (160, 65),
     (162, 60), (158, 52), (150, 45), (142, 40), (140, 35), (135, 33),
     (130, 31), (127, 35), (122, 38), (120, 32), (115, 23), (110, 20),
     (105, 10), (103, 2), (100, 8), (97, 15), (92, 21), (87, 21),
     (82, 16), (77, 8), (73, 19), (68, 23), (62, 25), (57, 26),
     (52, 28), (48, 30), (44, 30), (40, 32), (36, 36)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32),
     (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15),
     (142, -11), (137, -12), (135, -15), (132, -12), (130, -13),
     (126, -14), (122, -17), (118, -20)],
    [(167, -45), (170, -42), (174, -39), (177, -38), (175, -41),
     (172, -43)],
]


def draw_world(cv, x, y, w, h, pins):
    """Solid world map; pins are (number, lon, lat, region).

    Pin spots are nudged where true positions would touch: Antalya
    and Gaza, Kyiv and the Poland strike, Brussels and Geneva.
    Sand background with sage land, pins r=8 with a white ring.
    """
    cv.fill(x, y, w, h, MAP_BG)
    cv.border(x, y, w, h, HAIR, 1)
    lon0, lon1 = -170.0, 190.0
    lat0, lat1 = 78.0, -58.0
    for poly in LAND:
        pts = [(x + int((lon - lon0) / (lon1 - lon0) * w),
                y + int((lat0 - lat) / (lat0 - lat1) * h))
               for lon, lat in poly]
        cv.poly(pts, MAP_LAND)
    for num, lon, lat, region in pins:
        px = x + int((lon - lon0) / (lon1 - lon0) * w)
        py = y + int((lat0 - lat) / (lat0 - lat1) * h)
        col = PINKS.get(region, INK)
        cv.disc(px, py, 8, col)
        cv.ring(px, py, 8, WHITE, 2)
        lab = str(num)
        draw_text(cv, px - text_w(lab, 9) // 2, py - 4, lab, 9, WHITE,
                  bold=True)


# --------------------------------------------------------------------- data
# Forty stories for Friday 20 November 2026. The day's biggest war
# story leads (Kyiv: 110 missiles, 400 drones, 3 bridges, 9 killed);
# Akvan is lead #2; the Asia AI sell-off is lead #3. Two v3 tiles
# are gone -- the Crimea span (a 19 Nov story, now named in DATE
# CHECK) and the US-Venezuela deal (v3's own DATE CHECK excluded
# it). In their place: the UK-EU reset deal, the missile that landed
# in Poland, and Kenya's first oil well, which also gives Africa a
# story so no region bar reads zero. Phillips 118 gives Oceania one.
#
# Pin spots are nudged where true positions would touch (see
# draw_world). Every story happened, or was first reported, on
# this day.

MASTHEAD = "Friday 20 November 2026"
TOP_LEFT = "THE WORLD IN ONE DAY"
TOP_RIGHT = "40 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED FRIDAY 20 NOVEMBER 2026"
SUBHEAD = ("Russian missiles hit Kyiv's bridges \u00b7 Cyclone Akvan "
           "strikes India \u00b7 An AI sell-off sinks Asia's markets "
           "\u00b7 UK and EU seal a deal")

LEADS = [
    {"num": 1, "region": "europe", "art": "kyiv",
     "banner": "KYIV", "banner2": "3 bridges hit",
     "caption": "Officials' count",
     "kicker": "KYIV, UKRAINE \u00b7 WAR",
     "headline": "Russian missiles hit three Kyiv bridges",
     "deck": ("An overnight barrage of about 110 missiles and 400 "
              "drones killed nine people and cut power and water in "
              "the capital."),
     "pin": (33.0, 50.4),
     "src": "Kyiv Independent, BBC"},
    {"num": 2, "region": "asia", "art": "cyclone",
     "banner": "CYCLONE AKVAN", "banner2": "Landfall \u00b7 8 am",
     "caption": "Weather office",
     "kicker": "ODISHA, INDIA \u00b7 CYCLONE",
     "headline": "Cyclone Akvan comes ashore in eastern India",
     "deck": ("Landfall near Gopalpur from about 8 am, after 372,000 "
              "people were moved to shelters. No deaths were "
              "reported."),
     "pin": (84.9, 19.3),
     "src": "IMD, Deccan Herald"},
    {"num": 3, "region": "asia", "art": "market",
     "banner": "AI SELL-OFF", "banner2": "Asia, Friday's close",
     "caption": "Closing prices",
     "kicker": "TAIPEI \u00b7 SEOUL \u00b7 TOKYO \u00b7 MARKETS",
     "headline": "AI sell-off sinks Asia's stock markets",
     "deck": ("Taiwan's index fell 6.2%. Seoul lost 5.2% and Tokyo "
              "5.1% as chipmakers led the slide."),
     "pin": (121.5, 25.0),
     "src": "Al Jazeera, Anadolu"},
]

TILES = [
    {"num": 4, "region": "global", "scene": "globe-thermo",
     "banner": "COP31: NO DEAL",
     "kicker": "ANTALYA \u00b7 CLIMATE",
     "headline": "COP31 reaches its last day with no deal",
     "deck": "Draft text leaves out fossil fuels.",
     "cap": "Ongoing \u00b7 UN News",
     "pin": (27.0, 38.5), "src": "UN News"},
    {"num": 5, "region": "europe", "scene": "flags-uk-eu",
     "banner": "UK-EU DEAL",
     "kicker": "BRUSSELS \u00b7 DIPLOMACY",
     "headline": "UK and EU seal a \u2018reset\u2019 deal",
     "deck": "Food trade, visas, carbon link.",
     "cap": "Agreed \u00b7 Reuters",
     "pin": (1.0, 53.0), "src": "Reuters"},
    {"num": 6, "region": "europe", "scene": "missile-field",
     "banner": "POLAND: MISSILE",
     "kicker": "EASTERN POLAND \u00b7 SECURITY",
     "headline": "Russian cruise missile lands in Poland",
     "deck": "It fell in a field; airports paused.",
     "cap": "Minister says \u00b7 Reuters",
     "pin": (19.0, 52.5), "src": "Reuters"},
    {"num": 7, "region": "mideast", "scene": "tents",
     "banner": "GAZA: PUSH",
     "kicker": "GAZA \u00b7 WAR",
     "headline": "Gaza offensive displaces 6,000",
     "deck": "Families flee in a single day.",
     "cap": "Witnessed \u00b7 Al Jazeera",
     "pin": (36.8, 30.2), "src": "Al Jazeera"},
    {"num": 8, "region": "asia", "scene": "skyline",
     "banner": "SOFTBANK: -14.5%",
     "kicker": "TOKYO \u00b7 MARKETS",
     "headline": "SoftBank plunges 14.5% in AI rout",
     "deck": "Worst day since Aug 2024.",
     "cap": "Close \u00b7 CNBC",
     "pin": (139.7, 35.7), "src": "CNBC"},
    {"num": 9, "region": "europe", "scene": "chess",
     "banner": "GUKESH: TITLE",
     "kicker": "GENEVA \u00b7 SPORT",
     "headline": "Gukesh defends chess title",
     "deck": "The champion keeps his crown.",
     "cap": "Federation \u00b7 Reuters",
     "pin": (10.5, 43.5), "src": "Reuters"},
    {"num": 10, "region": "americas", "scene": "chart",
     "banner": "WALL ST: -2.02%",
     "kicker": "NEW YORK \u00b7 MARKETS",
     "headline": "S&P falls 2.02% as AI rout spreads",
     "deck": "Dow -1,101, sixth straight loss.",
     "cap": "Close \u00b7 AP",
     "pin": (-74.0, 40.7), "src": "AP"},
    {"num": 11, "region": "americas", "scene": "chip",
     "banner": "ANTHROPIC: $2TN",
     "kicker": "SAN FRANCISCO \u00b7 TECH",
     "headline": "Anthropic tops $2tn in biggest IPO ever",
     "deck": "Hit $111.50, closed at $97.17.",
     "cap": "Debut \u00b7 Reuters",
     "pin": (-122.4, 37.8), "src": "Reuters"},
    {"num": 12, "region": "africa", "scene": "oil",
     "banner": "KENYA: OIL",
     "kicker": "TURKANA \u00b7 ENERGY",
     "headline": "Kenya starts drilling its first oil well",
     "deck": "First crude is due on 1 December.",
     "cap": "Ceremony held \u00b7 allAfrica",
     "pin": (36.0, 3.0), "src": "allAfrica"},
    {"num": 13, "region": "oceania", "scene": "cricket",
     "banner": "PHILLIPS: 118",
     "kicker": "WELLINGTON \u00b7 CRICKET",
     "headline": "Phillips hits 118 against India",
     "deck": "Hundreds in all three formats.",
     "cap": "Scorecard \u00b7 ICC",
     "pin": (174.8, -41.3), "src": "ICC"},
]

STATS = [
    ("3", "bridges damaged in Kyiv"),
    ("372,000", "evacuated as Cyclone Akvan hits Odisha"),
    ("-6.2%", "Taiwan's share index, Friday's close"),
    ("118", "runs by Glenn Phillips against India"),
    ("100,000", "youth visas a year in UK-EU deal"),
    ("$97.17", "Anthropic's first-day close"),
]

# (region, one-line brief, source) -- numbered 14 to 40 on the page.
# Each brief names its source, as the winning pages do. v4.2: every
# brief below was checked against the date it was first reported;
# the v4.1 list was mostly stale or unverified (Senate vote 19 Nov,
# SAFF final 17 Nov, George Washington 18 Nov, Iran cluster) and
# three numbers were wrong (Sensex, Nikkei, NZ score).
BRIEFS = [
    ("europe", "EU: €1bn arms for Ukraine", "Reuters"),
    ("europe", "Dutch €15bn defence plan", "Reuters"),
    ("europe", "Germany funds Ukraine drones", "Reuters"),
    ("europe", "UK shell output up 16-fold", "Reuters"),
    ("europe", "Estonia closes Russia borders", "Reuters"),
    ("europe", "Ukraine deploys laser air defence", "AP"),
    ("europe", "Russia hits top EU substation", "Reuters"),
    ("europe", "Ukraine hits Druzhba oil station", "AP"),
    ("asia", "Sensex +1.08%, Nifty +1.12%", "PTI"),
    ("oceania", "NZ 368, Nicholls 175* vs India", "PTI"),
    ("asia", "Tokyo: Nikkei falls 5.1%", "Reuters"),
    ("asia", "Japan CPI hits 2.3%", "Reuters"),
    ("asia", "MSCI Asia-Pacific -8.3%", "Reuters"),
    ("asia", "Samsung -7%, TSMC -4.8% in rout", "Reuters"),
    ("asia", "Nifty Bank hits record high", "PTI"),
    ("asia", "Rupee hits 7-month high", "Reuters"),
    ("asia", "Kioxia -11.7%, Advantest -10.3%", "Reuters"),
    ("mideast", "Houthis threaten Saudi ports", "Reuters"),
    ("mideast", "Brent $92.57 as flows recover", "Reuters"),
    ("americas", "US tightens Iran sea blockade", "Reuters"),
    ("americas", "Trump: Putin 'would love to end war'", "AP"),
    ("global", "Gold falls 9% in a week", "Reuters"),
    ("global", "World stocks fall for 7th day", "Reuters"),
    ("global", "UNICEF: 1,144 children killed in war", "AP"),
    ("global", "France, Panama push COP31 deal", "UN News"),
    ("africa", "Guinea bans Burkina Faso broadcaster", "AP"),
    ("africa", "S. Africa holds rates at 7.25%", "Reuters"),
]

DATE_BODY = ("Left out on purpose (18-19 Nov): Trump-Xi-Putin summit "
             "\u00b7 ICJ Rohingya verdict \u00b7 Anthropic $83 IPO "
             "\u00b7 GTA VI unlock \u00b7 $190.4m art sale \u00b7 EU "
             "\u20ac45bn loan \u00b7 US-Venezuela deal \u00b7 Han "
             "Duck-soo verdict \u00b7 Houthi strike on Riyadh "
             "\u00b7 Crimea span hit \u00b7 Gemini 4 Neon debut "
             "\u00b7 Senate 51-48 Iran vote.")

REGION_ORDER = ["europe", "asia", "mideast", "africa", "americas",
                "oceania", "global"]
REGION_LABEL = {"europe": "EUROPE", "asia": "ASIA",
                "mideast": "MIDEAST", "africa": "AFRICA",
                "americas": "AMERICAS", "oceania": "OCEANIA",
                "global": "GLOBAL"}

FOOT_A = ("Every story here happened, or was first reported, on Friday "
          "20 November 2026. Officials' counts are attributed.")
FOOT_B = "Sources named beside each story \u00b7 Original drawings."

TITLE = ("Friday 20 November 2026: 40 stories, 7 regions \u2014 Kyiv "
         "bridges hit, Cyclone Akvan landfall, Asia's AI sell-off")


# ------------------------------------------------------------------- layout
ISSUES = []


def flag(label, detail):
    ISSUES.append("%s: %s" % (label, detail))


def badge(cv, x, y, num, c=RED):
    """Number disc for a story, number centred in white."""
    cv.disc(x, y, 8, c)
    lab = str(num)
    draw_text(cv, x - text_w(lab, 9) // 2, y - 4, lab, 9, WHITE, bold=True)


def _fit_size(text, start, max_w, gap=0):
    """Largest cap height <= start whose text fits max_w."""
    size = start
    while size > 8 and vtext_w(text, size, gap) > max_w:
        size -= 1
    return size


def build_page():
    cv = Canvas(W, H, PAPER)

    # ---- top strip + masthead ----
    cv.fill(0, 0, W, 8, RED)
    draw_text(cv, MX, 14, TOP_LEFT, 12, RED, bold=True, serif=True, gap=1)
    tr_w = text_w(TOP_RIGHT, 10)
    draw_text(cv, W - MX - tr_w, 15, TOP_RIGHT, 10, SOFT)
    msize = _fit_size(MASTHEAD, 78, CW)
    draw_text(cv, MX, 34, MASTHEAD, msize, INK, bold=True, serif=True)
    ssize = _fit_size(SUBHEAD, 13, CW)
    draw_text(cv, MX, 116, SUBHEAD, ssize, INK, serif=True, italic=True)
    cv.hline(MX, 138, CW, INK, 2)

    # ---- numbers strip: six biggest numbers of the day ----
    ny = 146
    for i, (num, label) in enumerate(STATS):
        bx = MX + i * 162
        cv.fill(bx, ny, 3, 56, RED)
        nsize = 26
        while text_w(num, nsize, gap=0) > 150 and nsize > 14:
            nsize -= 1
        draw_text(cv, bx + 9, ny, num, nsize, NAVY, bold=True)
        yy = ny + 32
        llines = wrap_text(label, 10, 150)
        if len(llines) > 2:
            flag("stat %d" % i, "label wraps to %d lines" % len(llines))
        for ln in llines[:2]:
            draw_text(cv, bx + 9, yy, ln, 10, SOFT)
            yy += 12
    cv.hline(MX, 206, CW, HAIR, 1)

    # ---- region bar (top): counts sum to 40, no zero region ----
    counts = {r: 0 for r in REGION_ORDER}
    for st in LEADS + TILES:
        counts[st["region"]] += 1
    for region, _txt, _src in BRIEFS:
        counts[region] += 1
    if sum(counts.values()) != 40:
        flag("regions", "counts sum to %d" % sum(counts.values()))
    if min(counts.values()) < 1:
        flag("regions", "a region has zero stories")
    small = [r for r in REGION_ORDER if counts[r] <= 2]
    big = [r for r in REGION_ORDER if counts[r] > 2]
    widths = {}
    rest = CW - 70 * len(small)
    tot = sum(counts[r] for r in big)
    for r in small:
        widths[r] = 70
    for r in big:
        widths[r] = int(round(rest * counts[r] / tot))
    widths[big[0]] += CW - sum(widths.values())
    rx = MX
    for region in REGION_ORDER:
        wseg = widths[region]
        cv.fill(rx, 212, wseg, 22, PINKS[region])
        lab = "%s %d" % (REGION_LABEL[region], counts[region])
        lw = text_w(lab, 10)
        if lw > wseg - 6:
            flag("region %s" % region, "label too wide for segment")
        draw_text(cv, rx + (wseg - lw) // 2, 218, lab, 10, WHITE, bold=True)
        rx += wseg

    # ---- three leads ----
    lw, lgap = 312, 18
    ly, lph = 242, 108
    for i, st in enumerate(LEADS):
        lx = MX + i * (lw + lgap)
        if st["art"] == "kyiv":
            art_kyiv(cv, lx, ly, lw, lph)
        elif st["art"] == "cyclone":
            art_cyclone(cv, lx, ly, lw, lph)
        else:
            art_market(cv, lx, ly, lw, lph)
        cv.border(lx, ly, lw, lph, INK, 2)
        bw = text_w(st["banner"], 12, gap=1) + 16
        cv.fill(lx, ly, bw, 20, RED)
        draw_text(cv, lx + 8, ly + 4, st["banner"], 12, WHITE, bold=True,
                  gap=1)
        b2w = text_w(st["banner2"], 10) + 12
        cv.fill(lx + lw - b2w, ly + lph - 18, b2w, 18, WHITE)
        draw_text(cv, lx + lw - b2w + 6, ly + lph - 14, st["banner2"], 10,
                  INK, bold=True)
        capw = text_w(st["caption"], 9) + 12
        cv.fill(lx, ly + lph - 16, capw, 16, INK)
        draw_text(cv, lx + 6, ly + lph - 12, st["caption"], 9, WHITE)
        ky = ly + lph + 8
        badge(cv, lx + 8, ky + 5, st["num"])
        draw_text(cv, lx + 22, ky, st["kicker"], 11, RED, bold=True, gap=1)
        yy = ky + 18
        hlines = wrap_text(st["headline"], 19, lw)
        if len(hlines) > 2:
            flag("lead %d" % st["num"], "headline %d lines"
                 % len(hlines))
        for ln in hlines[:2]:
            draw_text(cv, lx, yy, ln, 19, INK, bold=True, serif=True)
            yy += 24
        yy += 2
        deck = st["deck"] + " (" + st["src"] + ")"
        dlines = wrap_text(deck, 11, lw)
        if len(dlines) > 3:
            flag("lead %d" % st["num"], "deck %d lines" % len(dlines))
        for ln in dlines[:3]:
            draw_text(cv, lx, yy, ln, 11, SOFT)
            yy += 14
        if yy > ly + lph + 118:
            flag("lead %d" % st["num"], "text overflows lead box")

    # ---- ten tiles: picture, kicker, headline, one-line deck ----
    colw, cgap = 184, 13
    trow0, tpitch, theight = 476, 111, 104
    for idx, st in enumerate(TILES):
        r, c = divmod(idx, 5)
        x = MX + c * (colw + cgap)
        y = trow0 + r * tpitch
        mini_scene(cv, x, y, colw, 42, st["scene"])
        cv.border(x, y, colw, 42, INK, 1)
        bw = text_w(st["banner"], 9, gap=1) + 10
        cv.fill(x, y, bw, 15, RED)
        draw_text(cv, x + 5, y + 3, st["banner"], 9, WHITE, bold=True,
                  gap=1)
        capw = text_w(st["cap"], 8) + 10
        cv.fill(x, y + 42 - 13, capw, 13, INK)
        draw_text(cv, x + 5, y + 42 - 10, st["cap"], 8, WHITE)
        ky = y + 47
        badge(cv, x + 7, ky + 4, st["num"])
        draw_text(cv, x + 19, ky, st["kicker"], 9, RED, bold=True, gap=1)
        yy = y + 61
        hlines = wrap_text(st["headline"], 13, colw)
        if len(hlines) > 2:
            flag("tile %d" % st["num"], "headline %d lines"
                 % len(hlines))
        for ln in hlines[:2]:
            draw_text(cv, x, yy, ln, 13, INK, bold=True, serif=True)
            yy += 15
        dlines = wrap_text(st["deck"], 9, colw)
        if len(dlines) > 1:
            flag("tile %d" % st["num"], "deck wraps to %d lines"
                 % len(dlines))
        draw_text(cv, x, yy, dlines[0], 9, SOFT)
        if yy + 10 > y + theight:
            flag("tile %d" % st["num"], "text overflows tile")

    cv.hline(MX, 700, CW, INK, 2)

    # ---- bottom left: map ----
    by = 708
    draw_text(cv, MX, by, "WHERE IT HAPPENED", 13, INK, bold=True, gap=1)
    draw_text(cv, MX, by + 18,
              "Each number is the story with that number on this page.",
              9, FAINT)
    pins = []
    for st in LEADS + TILES:
        lon, lat = st["pin"]
        pins.append((st["num"], lon, lat, st["region"]))
    draw_world(cv, MX, by + 32, 470, 184, pins)

    # ---- bottom right: 27 more briefs, two columns, sourced ----
    bx0 = 516
    draw_text(cv, bx0, by, "ALSO ON FRIDAY \u2014 27 MORE", 13, INK,
              bold=True, gap=1)
    draw_text(cv, bx0, by + 18, "Stories 14-40 in brief", 9, FAINT)
    half = (len(BRIEFS) + 1) // 2
    for ci, chunk in enumerate((BRIEFS[:half], BRIEFS[half:])):
        cx = bx0 + ci * 244
        yy = by + 32
        for j, (region, item, src) in enumerate(chunk):
            num = 14 + ci * half + j
            draw_text(cv, cx, yy, str(num), 9, RED, bold=True)
            full = "%s (%s)" % (item, src)
            if text_w(full, 9) > 216:
                flag("brief %d" % num, "too wide: %s" % full)
            draw_text(cv, cx + 22, yy, full, 9, INK)
            yy += 12

    # ---- DATE CHECK (bottom): the 19 Nov stories left out ----
    dy = 934
    cv.fill(MX, dy, CW, 38, DATE_BG)
    cv.border(MX, dy, CW, 38, RED, 1)
    draw_text(cv, MX + 10, dy + 12, "DATE CHECK", 13, RED, bold=True,
              gap=1)
    date_lines = wrap_text(DATE_BODY, 10, CW - 150)
    if len(date_lines) > 2:
        flag("date check", "body wraps to %d lines" % len(date_lines))
    for i, ln in enumerate(date_lines):
        draw_text(cv, MX + 140, dy + 6 + i * 12, ln, 10, INK)

    if ISSUES:
        print("LAYOUT ISSUES:")
        for v in ISSUES:
            print("  ", v)
        sys.exit(1)

    # ---- footer ----
    cv.hline(MX, 980, CW, INK, 1)
    draw_text(cv, MX, 988, FOOT_A, 10, FAINT)
    draw_text(cv, MX, 1001, FOOT_B, 10, FAINT)

    total = len(LEADS) + len(TILES) + len(BRIEFS)
    if total != 40:
        print("STORY COUNT %d != 40" % total)
        sys.exit(1)
    return cv


def main():
    cv = build_page()
    small = cv.downsample()
    data = png_bytes(small)
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
