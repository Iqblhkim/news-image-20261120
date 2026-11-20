# news-image-20261120 — build notes (v1)

- Entry: 48 stories for Friday 20 November 2026, pure-stdlib Python 3.13
  (Canvas + 5x7 bitmap font + zlib PNG encoder, no network, no Pillow).
- Design: the approved news19 v4 preview layout, ported to pure stdlib —
  navy masthead, 3 illustrated panels (Shenzhen / Cyclone Akvan / IPO),
  3 featured stories, 10 illustrated medium tiles (5x2), BY THE NUMBERS
  strip, dotted world map with 13 numbered pins, region bars, 35 briefs.
- Font: hand-made 5x7 glyphs; verified visually — the v3 glyph bugs
  (g→9, y→u, z→7, E→F) are not present in this build.
- Bug found and fixed in review: the panel caption strip used x2/y2
  coordinates in a rect() that takes (x, y, w, h); it painted a giant
  navy block over the featured section. Fixed to (x, y, 312, 17).
- Determinism: two runs write byte-identical entry.png
  (sha256 e5ab42b2d64d63027162f9ec72dae4ff5c19f70f2b0b229f06b5b018679a2996,
  44,757 bytes, 1024x1024).
- Recording: NOT applicable — the CLI reports this competition "does
  not take recorded transcripts: its entries upload their transcripts
  (a bundle or loose files)". Transcripts are bundled by the parent
  at submit time, as for news19 v2/v3.
- Local kit check: run below (without transcripts; the transcript gate
  is evaluated with the bundle at submit time).
- NOT pushed, NOT submitted by this build. Parent pushes via browser
  and submits after verifying.
