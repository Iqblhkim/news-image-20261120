[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Iqblhkim/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Iqblhkim/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

# News in One Image — 20 November 2026

One image summing up the world's news of Friday 20 November 2026,
built for make.fun's "Sum up 20 November's world news in one image"
bounty ($250 in USDC).

The image is a newspaper-style front page, "THE WORLD IN ONE DAY":
a big lead story with a full illustration (the first-ever
Trump–Xi–Putin trilateral in Shenzhen ends with a joint declaration
on the UN, nuclear arms and oil), two picture panels (Cyclone Akvan
makes landfall on India's east coast at noon, 300,000 people moved
to safety; Anthropic closes its first Nasdaq day at $97.17, up 17%
on the record $81.3bn IPO), ten illustrated tiles (the Crimea bridge
is hit a third time; the COP31 closing draft drops every mention of
fossil fuels; the ICJ rules on the Myanmar genocide case; Russian
strikes damage the Dutch and Austrian embassies in Kyiv; Israel's
Gaza ground push displaces 6,000 people in a day; and more), a BY
THE NUMBERS strip, a dotted world map with numbered pins, region
bars, and 27 more one-line briefs — 40 stories in all.

## Run

The program draws the image itself, with the Python standard library
only — no network, no third-party packages:

```
python3 main.py
```

It writes `/output/entry.png` — running it twice writes the same bytes.
The image is a 1024x1024 PNG under 1 MiB.

## Versions

- v2: full redesign (40 stories, hero + 2 panels + 10 tiles + map +
  region bars), engine rewritten fresh in-session. See BUILD_NOTES.md.
- v1.1: 48 stories, "Neat Corona" — rank 904/1,687, judge 96.11%
  provisional; submitted 2026-11-20 08:08 WIB, claim
  AF-BFHAY-KFMSH-PCBV9-3PP7E.
