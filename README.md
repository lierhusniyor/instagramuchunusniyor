# uz-insta-agent

Har kuni: navbatdagi postni Instagram'ga joylaydi, akkaunt va trendlarni tahlil qiladi, hisobotni Telegram (yoki email) ga yuboradi.
Hammasi **Windsor.ai** orqali: Instagram Graph API, `IG_USER_ID` va Meta token kerak emas.

## Nima qiladi
- **Joylash**: `queue/posts.json` dagi navbatdagi post (rasm, karusel, reels, story) Windsor orqali joylanadi. Kuniga 1 ta.
- **Tahlil**: o'z akkauntingiz postlari (layk, izoh, qamrov, saqlash), eng yaxshi soatlar, teglar, so'zlar.
- **Trendlar**: Google Trends (ochiq RSS), O'zbekiston.
- **Telegram**: joylash natijasi va hisobot botingizga keladi.

## Nima QILMAYDI (ataylab)
- Instagram'ga login qilib skreyp qilmaydi.
- Boshqa bloggerlar postlarini tahlil qilmaydi: bu Graph API `IG_USER_ID` + token talab qiladi. Ro'yxat `config.json` da `watchlist` nomi bilan saqlangan, hozir ishlatilmaydi.
- iMessage qo'llab-quvvatlanmaydi.

## Sozlash
1. windsor.ai da Instagram (Business/Creator) akkauntni ulang. Key: Settings > API Access.
2. Telegram: @BotFather dan bot yarating, botga yozing, chat id ni @userinfobot dan oling.
3. `pip install -r requirements.txt`, `cp .env.example .env` va to'ldiring.
4. Sinov (tarmoqsiz): `python tests/make_sample.py && python run_daily.py --sample`
5. Ko'rish (joylamasdan): `python run_daily.py --post --dry-run`
6. Haqiqiy: `python run_daily.py --post`

## Post navbati (`queue/posts.json`)
```json
[
  {"id": "p1", "type": "image", "url": "https://.../rasm.jpg", "caption": "Kalit so'z ... savol? #teg1 #teg2", "date": "2026-10-23"},
  {"id": "p2", "type": "reel", "url": "https://.../video.mp4", "caption": "..."},
  {"id": "p3", "type": "carousel", "urls": ["https://.../1.jpg", "https://.../2.jpg"], "caption": "..."},
  {"id": "p4", "type": "story", "url": "https://.../story.jpg"}
]
```
- Havola **ochiq (public)** bo'lishi shart. Rasm: JPEG, <= 8 MB, nisbat 4:5 dan 1.91:1 gacha. Reels: MP4/MOV, 3 s - 15 min, 9:16.
- `date` ixtiyoriy: shu kundan oldin joylanmaydi.
- Joylangan postlar `state/posted.json` ga yoziladi va qayta joylanmaydi.

## Har kuni avtomatik
`.github/workflows/daily.yml` har kuni 08:00 (Toshkent) ishlaydi. Repo Settings > Secrets and variables > Actions ga `.env.example` dagi nomlar bilan secret qo'shing (kamida `WINDSOR_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).

## Holat
- Tahlil va navbat mantig'i testlarda sinalgan (`python -m unittest discover -s tests`).
- Windsor orqali o'qish (`get_data`) haqiqiy akkauntda sinalgan; joylash va Telegram yuborish haqiqiy tarmoqda hali sinalmagan. Xatolar hisobotning "Ogohlantirishlar" va "Joylash" qismida chiqadi.
