# uz-insta-agent

O'zbek Instagram bloggerlarini har kuni tahlil qilib, hisobotni Telegram yoki emailga yuboradi.

## Nima qiladi
- Google Trends (ochiq RSS) orqali O'zbekistondagi kunlik trend qidiruvlarni oladi.
- Instagram Graph API (Business Discovery) orqali `config.json` dagi akkauntlarning oxirgi postlarini oladi.
- Tahlil qiladi: joylash soati (Toshkent vaqti), engagement, teglar, so'zlar, bir necha blogger tilga olgan mavzular.
- Qisqa o'zbekcha hisobot yuboradi.

## Nima QILMAYDI (ataylab)
- Instagram'ga login qilib skreyp qilmaydi (Instagram qoidalariga zid, akkaunt bloklanadi).
- Business Discovery faqat ochiq Business/Creator akkauntlarni o'qiydi. Qolganlari hisobotda "o'tkazib yuborildi" deb chiqadi.
- Boshqa akkauntlarning ko'rishlar sonini odatda ko'ra olmaydi, shuning uchun engagement = (layk + izoh) / obunachi.
- iMessage qo'llab-quvvatlanmaydi.

## Sozlash
1. `pip install -r requirements.txt`
2. `cp .env.example .env` va qiymatlarni to'ldiring:
   - Telegram: @BotFather dan bot yarating, tokenni oling; botga yozing, chat id ni @userinfobot dan oling.
   - Instagram Graph API: developers.facebook.com da ilova yarating, Business/Creator Instagram akkauntingizni ulang, `IG_USER_ID` va `IG_ACCESS_TOKEN` oling.
3. Sinov (haqiqiy tarmoqsiz): `python tests/make_sample.py && python run_daily.py --sample`
4. Haqiqiy ishga tushirish: `python run_daily.py` (yoki `--dry-run`, yubormasdan ko'rish uchun)

## Har kuni avtomatik
GitHub Actions: `.github/workflows/daily.yml` har kuni 08:00 (Toshkent) ishga tushadi. Repo Settings, Secrets and variables, Actions bo'limiga `.env.example` dagi nomlar bilan secret qo'shing.

## Holat
- Analizator namuna ma'lumotda sinalgan (`python -m unittest discover -s tests`).
- Graph API va Google Trends chaqiruvlari haqiqiy tarmoqda hali sinalmagan; birinchi ishga tushirishda xatolar hisobotning "Ogohlantirishlar" qismida chiqadi.
- `graph_version` (config.json) eskirgan bo'lsa, Meta hujjatidagi joriy versiyaga o'zgartiring.
