# BAZA: ishlayotgan holat (2026-10-22)

Bu loyihaning birinchi ishlaydigan nuqtasi. Keyingi ishlar shu asosda quriladi.

## Nima ishlaydi (jonli sinalgan)
- Windsor.ai orqali Instagram `usniy_or` ga rasm joylash (media id 18106020551625510).
- Windsor orqali akkaunt ma'lumotini o'qish (`get_data`).
- GitHub Actions orqali Telegram botga xabar yuborish (`telegram-xabar.yml`, `notify/message.txt` o'zgarsa ishlaydi).
- Kunlik workflow: testlar, tahlil, Telegram hisobot.

## Hali jonli sinalmagan
- `run_daily.py --post` bilan navbatdan joylash (`queue/posts.json` hozir bo'sh).
- Reels, karusel, story joylash.
- Google Trends RSS.

## Sirlar
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WINDSOR_API_KEY`: faqat GitHub Secrets'da. Kodga yozilmaydi.

## Qoidalar
- CLAUDE.md dagi kontent qoidalari doimiy.
- Instagram bilan faqat Windsor orqali (Graph API / IG_USER_ID yo'q).

## Keyingi qadamlar
1. `queue/posts.json` ni to'ldirib, kunlik avtomatik joylashni sinash.
2. Hisobotga "bugungi reel g'oyasi".
3. `reels/` videolarini ochiq havolaga chiqarish.

## Tarix
- Birinchi muvaffaqiyat: Claude bilan Telegram orqali ishlab, "Salom, dunyo" posti va bot xabari.
