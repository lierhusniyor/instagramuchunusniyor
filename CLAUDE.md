# Claude uchun yo'riqnoma (shu loyiha)

## Foydalanuvchi
- O'zbek tilida yozadi. Javoblar QISQA bo'lsin.
- Maqsad: Instagram haqida kanal yuritish va o'zbek bloggerlar trendlarini kuzatish. Kanal kontentini Claude yasaydi (matnli reels, caption, teglar), akkauntni foydalanuvchi o'zi ochadi.

## Doimiy kontent qoidalari (kelishilgan, har doim amal qilinadi)
- Bitta yo'nalish: Instagram haqida.
- Videoning birinchi 2 soniyasida kuchli ilgak.
- Video qisqa: 7-20 soniya.
- Caption boshida kalit so'z, oxirida savol.
- Har postda 3-5 ta teg.
- Muntazam joylash (kuniga 1 ta), izohlarga tez javob.
- Natijani hech qachon kafolatlama. Qoida eskirgan yoki noto'g'ri bo'lsa, ochiq ayt.

## Texnik chegaralar
- Instagram'ga login qilib skreyp qilma. Faqat rasmiy API va ochiq manbalar.
- Sirlar (token, parol) hech qachon kodga yoki GitHub'ga yozilmaydi: faqat `.env` / GitHub Secrets.
- Bepul rejada Claude o'zi jadval bo'yicha ishlamaydi: kunlik ishni GitHub Actions bajaradi.

## Tuzilma
- `run_daily.py`: asosiy kirish nuqtasi (`--sample`, `--dry-run`).
- `agent/graph_api.py`, `agent/trends.py`: ma'lumot yig'ish.
- `agent/analyze.py`: tahlil. `agent/report.py`: hisobot matni. `agent/notify.py`: Telegram/email.
- `tests/`: sinovlar va sun'iy namuna ma'lumot.
- `reels/`: video generator (`make_reel.py`, `build_all.py`).

## Yaxshilash g'oyalari (navbat)
1. Birinchi haqiqiy ishga tushirishdan keyin Graph API/Trends xatolarini tuzatish.
2. `data/` dagi kunlik snapshotlardan haftalik trend taqqoslash.
3. Hisobotga "bugungi reel g'oyasi" bo'limi: trend + umumiy mavzu asosida.
4. Videolarga ovoz (TTS) va musiqa qo'shish.
5. Instagram Graph API orqali reelni avtomatik joylash (Business akkaunt kerak).

## O'zgarishlar jurnali
- 2026-10-21: loyiha yaratildi, analizator namuna ma'lumotda sinaldi.
