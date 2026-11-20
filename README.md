[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Iqblhkim/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Iqblhkim/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

# News in One Image — 20 November 2026

One image summing up the world's news of Friday 20 November 2026,
built for make.fun's "Sum up 20 November's world news in one image"
bounty ($250 in USDC).

The image is a newspaper-style front page: the first-ever Trump–Xi–Putin
trilateral in Shenzhen ends with a joint declaration on the UN, nuclear
arms and oil; Cyclone Akvan makes landfall on India's east coast at
noon, 300,000 people evacuated; Anthropic closes its first Nasdaq day
at $97.17, up 17% on the record $81.3bn IPO; the Crimea bridge is hit
a third time; the COP31 closing draft drops every mention of fossil
fuels; the ICJ rules on the Myanmar genocide case; Russian strikes
damage the Dutch and Austrian embassies in Kyiv; and Israel's Gaza
ground push displaces 6,000 people in a day — 48 stories in all, in
the winning layout: three illustrated panels, three featured stories,
ten illustrated tiles, a BY THE NUMBERS strip, a dotted world map
with numbered pins, region bars, and 35 more one-line briefs.

## Run

The program draws the image itself, with the Python standard library
only — no network, no third-party packages:

```
python3 main.py
```

It writes `/output/entry.png` — running it twice writes the same bytes.
The image is a 1024x1024 PNG under 1 MiB.
