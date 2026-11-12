# Claude uchun yo'riqnoma (shu loyiha)

## Foydalanuvchi
- O'zbek tilida yozadi. Javoblar QISQA bo'lsin.
- Maqsad (2026-11-02 dan): o'rganish va hayotini o'zgartirmoqchi bo'lgan hamma uchun kanal (o'rganish, IT, AI, intizom, kasb, sog'liq, til). Kanal kontentini Claude yasaydi (matnli reels, caption, teglar), akkauntni foydalanuvchi o'zi ochadi.

## Doimiy kontent qoidalari (kelishilgan, har doim amal qilinadi)
- Bitta yo'nalish: o'rganish va hayotni o'zgartirish (hamma uchun).
- Videoning birinchi 2 soniyasida kuchli ilgak.
- Video qisqa: 7-20 soniya.
- Caption boshida kalit so'z, oxirida savol.
- Har postda 3-5 ta teg.
- Muntazam joylash (kuniga 1 ta), izohlarga tez javob.
- Natijani hech qachon kafolatlama. Qoida eskirgan yoki noto'g'ri bo'lsa, ochiq ayt.

## Texnik chegaralar
- Instagram'ga login qilib skreyp qilma. Instagram bilan faqat Windsor.ai (MCP) orqali ishla; Graph API / IG_USER_ID ishlatilmaydi.
- Sirlar (token, parol) hech qachon kodga yoki GitHub'ga yozilmaydi: faqat `.env` / GitHub Secrets.
- Bepul rejada Claude o'zi jadval bo'yicha ishlamaydi: kunlik ishni GitHub Actions bajaradi.

## Tuzilma
- `run_daily.py`: asosiy kirish nuqtasi (`--sample`, `--dry-run`, `--post`).
- `agent/windsor.py`: Windsor MCP mijozi (o'z akkaunt ma'lumoti, joylash). `agent/trends.py`: Google Trends.
- `agent/poster.py`: `queue/posts.json` dan kunlik joylash, holat `state/posted.json`.
- `agent/analyze.py`: tahlil. `agent/report.py`: hisobot matni. `agent/notify.py`: Telegram/email.
- `tests/`: sinovlar va sun'iy namuna ma'lumot.
- `reels/`: video generator (`make_reel.py`, `build_all.py`).
- `reels/daily/`: kunlik avtomatik Reels. `make_video.py` ("180 kun" uslubi Axror prezentatsiyasidan: qorong'i fon #15141B, #FF6A2B, #3FC8E8, krem; Oswald/Rubik/JetBrains Mono; sahnalar: terminal+ilgak, [TIZIM] oynasi, krem karta, to'q sariq bayonot, konfetti final; "KUN N/180" progress; qahramon yo'q; ovoz edge-tts SardorNeural + musiqa), `scripts.json` (180 ta ssenariy h001-h180, kuniga 1 ta, ishlatilmagan birinchisi tanlanadi; eski 30 ta Instagram ssenariysi `scripts_instagram.json`da), `build_today.py` (navbatga qo'shadi). `daily.yml` har kuni 16:00 UTC (19:00 Moskva) yasaydi va joylaydi.

## Yaxshilash g'oyalari (navbat)
1. Birinchi haqiqiy ishga tushirishdan keyin Graph API/Trends xatolarini tuzatish.
2. `data/` dagi kunlik snapshotlardan haftalik trend taqqoslash.
3. Hisobotga "bugungi reel g'oyasi" bo'limi: trend + umumiy mavzu asosida.
4. Videolarga ovoz (TTS) va musiqa qo'shish.
5. `reels/` dagi videolarni ochiq havolaga chiqarib, navbatga avtomatik qo'shish.

## O'zgarishlar jurnali
- 2026-10-21: loyiha yaratildi, analizator namuna ma'lumotda sinaldi.
- 2026-10-22: Graph API olib tashlandi; Windsor orqali tahlil, joylash va Telegram birlashtirildi.
- 2026-10-30: kunlik avtomatik video: vektor qahramon Usniy, 30 ssenariy, 19:00 Moskva vaqtida yasash+joylash.
- 2026-11-02: yo'nalish o'zgardi: o'rganish/hayotni o'zgartirish, 180 ta ssenariy (6 oy, kuniga 1 ta). Oxirgi eski post: d03 (2026-11-01).
- 2026-11-02: Usniy qahramoni olib tashlandi (foydalanuvchiga yoqmadi); videolar Axror prezentatsiyasi uslubida qayta yasaldi, hamma uchun motivatsiya.
- 2026-11-12: 11-noyabr post joylanmadi (Ubuntu mirror DNS xatosi, ffmpeg o'rnatilmadi). daily.yml: apt 3 marta qayta urinadi, bo'lmasa setup-ffmpeg zaxirasi.
