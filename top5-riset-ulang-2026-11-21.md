# Riset Ulang Leaderboard news-image-20261120 — v3 vs Top 10

**Tanggal riset:** 21 Nov 2026, ~01:40 WIB (snapshot leaderboard via API, 10.340 entri scored)
**Bounty:** news-image-20261120 ($250, tutup 22 Nov 2026 07:00 WIB)
**Entri kita v3 "The World Today":** submission `01a1f9b0-4e2b-7169-adec-23f8339452c2`, **rank 4.453/10.340, judge 96,3451%** (interval 95,16–97,53%), W10-D0-L2, semua validity check PASS. Kuota 0/3 — v3 FINAL, riset ini untuk pelajaran bounty besok (20261121).
**Metode:** leaderboard diunduh (20,3 MB), artifact/screenshot publik top 10 + rank 40/50/60 diunduh dan DILIHAT langsung, dibandingkan sisi-per-sisi dengan artifact v3 kita (`/api/submissions/01a1f9b0.../artifact.webp`, sha256 `beed3a0f...` — SAMA dengan entry.png v3 yang di-submit).

> ⚠️ KOREKSI FILE: `~/workspace/makefun/news-image-20261120/entry.png` di disk ternyata masih **v2** (sha256 `b1d086d3...`, 48.450 byte, 20 Nov 04:16) — BUKAN v3. Perbandingan di laporan ini memakai artifact webp v3 yang di-submit (terverifikasi via sha256 leaderboard). Jangan pakai entry.png lokal untuk menilai v3.

## 1. Top 10 (snapshot 01:40 WIB — 9 dari 10 BERUBAH sejak snapshot 11:45 WIB kemarin)

| # | Handle | Judge | Judul submission |
|---|--------|-------|------------------|
| 1 | samatch-we | 99,2057% | Friday 20 November 2026: 35 stories, 7 regions — Kyiv bridges hit, Cyclone Akvan landfall, Asia's AI sell-off, UK-EU deal |
| 2 | 888dao-sats | 99,1652% | Friday 20 November 2026: 36 stories, 6 continents — Cyclone Akvan landfall, Kyiv ballistic missiles, COP31 final day deadlock |
| 3 | kiencx | 99,1429% | Friday 20 November 2026: 33 sourced stories, 13 drawn — Kyiv barrage, Cyclone Akvan landfall, Asia's AI sell-off |
| 4 | dewacandra4 | 99,1336% | Friday 20 November 2026: 38 stories from one day, 7 regions — Kyiv bridges hit, Cyclone Akvan landfall, UK-EU reset deal, AI sell-off; every figure attributed |
| 5 | mellow-otter-50 | 99,1332% | Friday 20 November 2026 — The Day in World News |
| 6 | kho22 | 99,1137% | Friday 20 November 2026 front page |
| 7 | madsrepo | 99,1034% | Friday 20 November 2026: the day in world news |
| 8 | mangmang | 99,0652% | Friday 20 November 2026: 36 stories, 7 regions — cyclone, Kyiv, COP31 |
| 9 | kim-soleum | 99,0534% | Friday 20 November 2026: 34 sourced stories, 7 regions — Cyclone Akvan landfall, Russia's mass strike on Ukraine, UK-EU reset deal, global AI sell-off; date-checked |
| 10 | aryanpatelx | 99,0412% | Friday 20 November 2026: 33 sourced stories, 13 drawn — Kyiv barrage, Cyclone Akvan landfall, Asia's AI sell-off |

**Zona cutoff:** #40 = 98,9026% · **#50 = 98,8540%** · #60 = 98,8396% · #100 = 98,7122% · #500 = 98,2336% · #1000 = 97,8644% · #2000 = 97,4085% · median = 95,9408%.
**Gap kita:** ke #50 **+2,51 poin** · ke #10 +2,70 · ke #1 +2,86. Bahkan batas ATAS interval kita (97,53%) masih di sekitar rank ~1.900. Gap ini BUKAN noise — ini struktural.

**Churn:** hanya kho22 yang bertahan di top 10 sejak snapshot pagi (dulu #1, kini #6, skor sama 99,1137%). Leaderboard masih bergerak — entri terus masuk (9.395 → 10.340 scored dalam sehari).

**Rank 3 = rank 10: template yang sama, dua kali.** Judul submission #3 dan #10 IDENTIK kata-per-kata ("33 sourced stories, 13 drawn — Kyiv barrage, Cyclone Akvan landfall, Asia's AI sell-off"), daftar cerita, angka, dan teks DATE CHECK sama; render pikselnya berbeda (mean abs diff 49,6/kanal — dua render berbeda, bukan copy file). Keduanya top 10. **Kesimpulan: yang dinilai juri adalah template/gaya itu sendiri — template pemenang itu reproducible, bukan keunikan sekali jadi.**

## 2. Pola Top 10 — konsisten di 10 besar vs hanya di 1–5

### Konsisten di 10/10 (atau 9/10) — ini template kanoniknya
1. **Masthead serif besar "Friday 20 November 2026"** (9/10 serif; #7 sans bold tapi tetap huruf sungguhan, bukan pixel). Judul submission 8/10 menyebut tanggal + jumlah cerita + 3–4 berita terbesar.
2. **Numbers strip = tepat 6 angka**, langsung di bawah subhead. Isinya angka TERBESAR hari itu: 300.000+ evakuasi, −6,2% Taiex, 118 Phillips, 3 jembatan, $97,17 Anthropic, 51–48 vote Senat, 8 tahun BepiColombo, 60,7% pil kanker, $48,3bn biaya perang Iran.
3. **Region bar/pills dengan hitungan yang jumlahnya = total cerita** (10/10), ditaruh di ATAS (di bawah numbers strip, sebelum lead). Tidak ada region 0.
4. **3 lead besar berilustrasi + 10 tile berilustrasi = 13 berilustrasi** (9/10; #4 punya 4 lead + 10 tile, #9 punya 4 lead + 8 tile). Lead #1/#2 SELALU Kyiv + Akvan (5/10 Akvan #1, 5/10 Kyiv #1); lead #3 = AI sell-off / COP31 / EU–UK deal.
5. **DATE CHECK box (berbingkai merah) di BAWAH halaman** (10/10), menyebut berita 19 Nov yang SENGAJA dikeluarkan (4–11 item). Varian terbaik juga menyebut yang BELUM terjadi ("any COP31 outcome, and Asia's closing prices" — #3/#10) dan yang terjadi SETELAH Jumat ("Turin's ATP Finals title match (Sun 22)" — #5).
6. **Footer klaim freshness + sumber bernama** (10/10): "Every story here happened, or was first reported, on Friday 20 November 2026" + "Sources: Reuters, AP, AFP, BBC, ..." + "Original drawings".
7. **Atribusi sumber per cerita di lead/tile** (10/10): "(Reuters)", "(AP)", "(AFP)" di akhir deck, atau "Source: X" di bawah headline.
8. **Kertas krem, serif + sans bersih, aksen merah** (10/10). Ilustrasi = gambar vektor datar yang SPESIFIK per cerita (skyline malam + jejak rudal + api; spiral radar + garis pantai; grafik saham merah + 4 kota; globe + termometer; bulan + pesawat antariksa; bendera).
9. **Jumlah cerita 32–44** (32, 33, 33, 34, 35, 36, 36, 36, 38, 44) — hitungan BUKAN penentu rank.
10. **Peta WHERE IT HAPPENED solid (terang atau navy gelap) + pin bernomor + caption** (9/10 — #8 TIDAK PUNYA PETA dan tetap #8; peta membantu tapi bukan wajib).

### Yang HANYA muncul di 1–5 — sejujurnya: hampir tidak ada pola tajam
- Perbedaan #1–5 vs #6–10 itu marginal (0,17 poin dari #1 ke #10) dan lebih ke polish ilustrasi + panjang DATE CHECK, bukan fitur biner. Yang paling dekat dengan "cuma di 1–5": (a) subhead italic berisi 4 headline ada di #1, #2, #3 (dan #6, #8, #9, #10 juga punya — jadi bukan pembeda); (b) tag kejujuran inline (`[FORECAST]`, `[CLAIM]`, chip "Officials say / Reported / Ongoing / Estimate") ada di #3/#10 dan #4 — tersebar, bukan monopoli 1–5.
- **Jurang yang sesungguhnya adalah top-60 vs sisanya**, bukan 1–5 vs 6–10. Bukti: rank #50 (98,8540%) vs #60 (98,8396%) cuma beda 0,01 poin, tapi keduanya JAUH di atas kita (2,5 poin). Dan rank #50 pun sudah menunjukkan cacat yang tidak ada di top 10 (lihat §3).

### Zona cutoff (rank 40 / 50 / 60) — apa yang memisahkan mereka dari top 10
- **#40 (ihza-fajar, 98,9026%):** template kanonik lengkap — serif, 6 angka, region bar, 3 lead (Akvan/Kyiv/COP31), 10 tile, peta navy, ALSO 23 cerita, DATE CHECK 8 item. Praktis tidak ada cacat kasat mata; kalah tipis dari top 10 di polish ilustrasi (label "144 TO 80 PARAGRAPHS" di panel COP31 agak aneh).
- **#50 (adinkadera, 98,8540%):** MULAI CACAT — (a) subhead merah MENABRAK descender masthead (teks overlap); (b) numbers strip cuma 5 angka; (c) TANPA region bar; (d) ilustrasi lead bergaya foto-AI (spiral satelit fotorealistis, gedung summit fotorealistis) bukan vektor datar; (e) DATE CHECK tidak konsisten: mengeluarkan 5 cerita 19 Nov tapi tile-nya sendiri berisi cerita 19 Nov lain (Houthi Riyadh, Fiji, Han Duck-soo, US–Venezuela).
- **#60 (witty-beacon-66, 98,8396%):** template kanonik tapi (a) region bar ASIA-PACIFIC 19 dari 36 (distribusi timpang), (b) ada tile "GEMINI 4 NEON 1M" — Gemini 4 Neon itu berita 18 Nov (dikeluarkan DATE CHECK #50!), (c) strip atas berisi 5 kotak tanggal/jam yang membingungkan.
- **Pelajaran dari cutoff:** yang membedakan 98,85% dari 96,35% bukan satu fitur ajaib — melainkan TIDAK ADANYA cacat kasat mata + konsistensi freshness + tipografi sungguhan.

## 3. Gap v3 vs Top 10 — per item, dengan bukti

### GAP 1 — Tipografi: font pixel 5×7 untuk SEMUA teks (terbesar, paling terlihat)
- **Pemenang:** serif masthead + sans body yang terbaca bersih bahkan di thumbnail 512px. Semua 10 besar.
- **v3:** masthead, headline, deck, brief, DATE CHECK, angka — SEMUA font bitmap 5×7. Di tampilan penuh 1024px (ukuran yang dilihat juri) halaman v3 kelihatan seperti printout dot-matrix; di zoom 2x headline "Cyclone Akvan hits Odisha" memang kebaca, tapi "Landfall near Gopalpur at noon; 300,000 moved as winds hit 110 km/h." terpecah jadi 3 baris dengan "km/h." yatim di baris ketiga. Huruf 'g' memang sudah dihindari di semua teks (BUILD_NOTES), tapi harga yang dibayar: font tetap terlihat kasar vs serif.
- **Perkiraan dampak:** BESAR — ini hal pertama yang dilihat juri di perbandingan berdampingan, dan membedakan v3 dari SEMUA 10 besar sekaligus. Kemungkinan penyumbang gap terbesar.

### GAP 2 — Urutan layout menyimpang dari kanonik
- **Pemenang:** masthead → subhead → numbers strip → region bar → 3 lead → 10 tile → peta → ALSO → DATE CHECK → footer.
- **v3:** masthead → subhead → lead → tile → **DATE CHECK (tengah halaman)** → **numbers strip (tengah halaman)** → peta + region bar (bawah peta) → ALSO → footer. DATE CHECK dan numbers strip ditaruh di tengah, region bar di bawah peta. Juri membandingkan screenshot berdampingan — urutan yang "salah tempat" langsung kelihatan.
- **Perkiraan dampak:** BESAR — struktur adalah hal kedua yang dinilai setelah tipografi.

### GAP 3 — Numbers strip cuma 4 angka, isinya lemah
- **Pemenang:** 6 angka, angka terbesar hari itu (3 jembatan, 300.000+, −6,2%, 118, 51–48, $97,17).
- **v3:** 4 angka — $97,17 (Anthropic), 300.000 (Akvan), **92.000 delegasi COP31**, **2.500 rudal Iran**. Dua slot dari empat diisi angka obscure (delegasi COP31, rudal Iran) sementara angka-angka kuat hari itu (3 jembatan Kyiv, 118 Phillips, 51–48 vote Senat, −6,2% Taiex) tidak dipakai.
- **Perkiraan dampak:** SEDANG–BESAR — strip angka adalah elemen signature di atas halaman; 4 vs 6 langsung terasa "kurang padat data".

### GAP 4 — Kyiv dikubur jadi tile kecil; berita perang terbesar tidak jadi lead
- **Pemenang:** Kyiv SELALU lead #1 atau #2, dengan detail spesifik (110 rudal + 400 drone, 3 jembatan, 9 tewas, 01:25 LOCAL) + ilustrasi malam berapi.
- **v3:** lead #1 Akvan (benar, dalam pola), lead #2 COP31, lead #3 Anthropic — tapi Kyiv cuma tile #8 "Kyiv strikes hit two embassies" (tanpa angka korban/jembatan/rudal). Berita terbesar hari itu dari sisi perang justru jadi tile kecil.
- **Perkiraan dampak:** BESAR — bobot konten. Juri membandingkan "apakah halaman ini memuat berita terbesar hari ini dengan bobot yang pantas".

### GAP 5 — Kontradiksi freshness INTERNAL (2 pelanggaran)
- **Pemenang:** DATE CHECK dan isi halaman konsisten 100% — yang di-exclude TIDAK PERNAH muncul sebagai cerita (cek #1, #2, #6: trilateral, ICJ, Anthropic $83, GTA VI, Van Gogh, dll. tidak ada di halaman mereka).
- **v3:** (a) **Tile #11 "US and Venezuela restore ties"** padahal DATE CHECK v3 sendiri mencantumkan **"US–Venezuela deal"** sebagai yang dikeluarkan. (b) **Tile #4 "Crimea span hit for third time"** — serangan Jembatan Crimea adalah berita 19 Nov menurut DATE CHECK rank #3/#6/#10 (mereka mengeluarkannya). Tile #4 ini diwarisi dari v2 tanpa diaudit ulang; riset top-5 sebelumnya sudah menandai tile basi v2 (#9 GTA, #12 Han, #13 Fiji) tapi #4 lolos dari audit.
- **Perkiraan dampak:** BESAR — freshness adalah kriteria eksplisit bounty ini ("every story dated Friday 20 November"); kontradiksi internal adalah sinyal yang paling mudah ditangkap juri dan paling merusak kepercayaan.

### GAP 6 — Ilustrasi tile terlalu kecil/generik
- **Pemenang:** tiap tile punya gambar mini SPESIFIK setinggi ~40% tile (bendera UK/EU, grafik saham, globe, raket kriket, pil, bulan, tank, chip).
- **v3:** tile cuma punya ikon glyph kecil (~20px) di atas kicker — halaman jadi dominan teks, "kurang digambar". Hero + 2 panel v3 lumayan (spiral radar, skyline oranye, candlestick), tapi 10 tile-nya kalah jauh dari tile pemenang.
- **Perkiraan dampak:** SEDANG — terlihat di perbandingan berdampingan; tile adalah 10 dari 13 slot berilustrasi.

### GAP 7 — Subhead = klaim meta, bukan ringkasan berita
- **Pemenang (7/10):** subhead italic berisi 4 headline terbesar ("Russian missiles hit Kyiv's bridges · Cyclone Akvan strikes India · An AI sell-off sinks Asia's markets · UK and EU seal a deal").
- **v3:** subhead = "Every story on this page happened, or was first reported, on this day." — klaim generik yang tidak memberi info berita apa pun. Klaim freshness seperti ini ditaruh pemenang di FOOTER, bukan di bawah masthead.
- **Perkiraan dampak:** SEDANG — baris paling menonjol kedua setelah masthead terbuang.

### GAP 8 — Region bar di bawah peta + OCEANIA 0
- **Pemenang:** region bar di atas lead, semua region ≥1 cerita (atau digabung ke WORLD/GLOBAL).
- **v3:** region bar di bawah peta; **OCEANIA 0** — bar dengan hitungan nol terlihat seperti lubang data. Total tetap 40 (Americas 7, Asia 11, Europe 9, Middle East 10, Oceania 0, Global 3).
- **Perkiraan dampak:** KECIL–SEDANG — murah diperbaiki, tapi kelihatan.

### GAP 9 — ALSO list tanpa atribusi per item; peta pendek
- **Pemenang:** 6/10 ALSO list mencantumkan sumber per item ("(Reuters)", "(AP)"); peta ~180–220px dengan pin besar.
- **v3:** ALSO 27 brief tanpa sumber per item; peta cuma 128px, pin kecil. (Catatan: 4/10 top-10 juga tanpa sumber di ALSO, dan #8 tanpa peta sama sekali — jadi ini BUKAN penentu, hanya polish.)
- **Perkiraan dampak:** KECIL.

### Yang BUKAN gap (v3 sudah benar)
- Lead #1 Akvan — dalam pola (5/10 lead Akvan). Judul masthead tanggal — benar. 40 cerita — dalam rentang 32–44. 3 lead + 10 tile = 13 berilustrasi — benar. DATE CHECK ada + 10 item — benar (isinya bagus; yang salah penempatan + konsistensinya). Peta solid + pin bernomor — benar. Atribusi "Source: X" di lead/tile — benar. Kertas krem + aksen merah — benar.

## 4. Kenapa v3 kalah 2,51 poin — ringkasan
Bukan satu kesalahan fatal, melainkan **tumpukan 5 gap BESAR yang semuanya terlihat dalam 3 detik pertama perbandingan berdampingan**: (1) font pixel vs serif, (2) urutan layout menyimpang, (3) Kyiv dikubur, (4) 2 kontradiksi freshness internal, (5) numbers strip 4 angka lemah — ditambah tile kurang bergambar dan subhead terbuang. v2 (95,68%) → v3 (96,35%) naik cuma +0,67 karena v3 memperbaiki hal-hal yang benar (DATE CHECK, peta solid, atribusi, lead Akvan) TAPI tidak menyentuh 5 gap di atas. Skor median seluruh bounty 95,94% — v3 cuma sedikit di atas median.

## 5. Aksi untuk news-image-20261121 besok (terurut, konkret)

1. **BUANG font pixel 5×7 — pakai huruf sungguhan.** Ini prioritas #1 dan prasyarat semua yang lain. Dalam pure stdlib: naikkan grid glyph (mis. 9×13 atau 12×16 dengan anti-aliasing abu-abu manual) ATAU gambar huruf kapital serif sebagai polygon. Target verifikasi SEBELUM submit: render masthead + 3 headline di thumbnail 512px dan bandingkan keterbacaannya dengan screenshot rank #1 — kalau masih kelihatan "komputer 1980-an", jangan submit.
2. **Pakai urutan kanonik persis:** masthead → subhead (4 headline) → numbers strip 6 angka → region bar → 3 lead → 10 tile → peta (≥180px) → ALSO → DATE CHECK → footer. Jangan pindahkan elemen.
3. **Pilih lead dari berita terbesar HARI ITU (21 Nov), bukan dari daftar kemarin:** 2 dari 3 slot lead harus berita dengan angka paling kuat (korban/rudal/evakuasi/indeks). Jangan pernah kubur berita perang/bencana terbesar jadi tile.
4. **Audit freshness 2 arah sebelum submit:** (a) tiap dari 13 cerita berilustrasi dicek tanggalnya — kalau ragu, turunkan ke ALSO atau buang; (b) tiap item di DATE CHECK dipastikan TIDAK MUNCUL di halaman mana pun (v3 gagal di sini 2x). Buat daftar exclude DULU dari berita 20 Nov, baru pilih cerita.
5. **Numbers strip = 6 angka TERBESAR hari itu** (korban, evakuasi, % indeks, skor olahraga, hasil vote, harga IPO) — jangan isi slot dengan angka obscure (delegasi konferensi, stok rudal).
6. **Tile = gambar mini spesifik setinggi ~40% tile** (bukan ikon glyph kecil). Alokasikan waktu gambar per tile, bukan cuma hero/panel.
7. **Subhead = 4 headline terbesar (italic); klaim freshness pindah ke footer. Region bar di atas, tanpa region 0** (kalau Oceania kosong, gabung ke Global atau cari 1 cerita Oceania). ALSO beri "(Sumber)" per item kalau sempat.
8. **Judul submission deskriptif:** "Friday 21 November 2026: N stories, M regions — [3 berita terbesar]" (8/10 top-10 begitu; judul v3 "The World Today" tanpa tanggal/hitungan adalah yang terlemah).
9. **Verifikasi visual berdampingan vs top-10 HARI BERJALAN sebelum submit** (template pemenang 21 Nov bisa dilihat dari leaderboard pagi — top 10 kemarin 9/10-nya pendatang baru, template bisa bergeser). Quality gate tetap berlaku: submit hanya kalau perbandingan visual menunjukkan kita setara template pemenang.

## Sumber data
- Leaderboard: `GET /api/competitions/news-image-20261120/leaderboard` (20,3 MB, 10.340 entri, snapshot 21 Nov 2026 ~01:40 WIB; file `/tmp/lb-news20-20261121.json`).
- Artifact: 14 screenshot webp di `/tmp/news20-top10/` (top 10 + rank 40/50/60 + v3 kita).
- Riset top-5 sebelumnya: `~/workspace/makefun/top5-research-2026-11-20.md` §3.
- Detail v3: `~/workspace/makefun/news-image-20261120/BUILD_NOTES.md` (bagian v3).
