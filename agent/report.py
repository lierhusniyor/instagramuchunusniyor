"""Tahlil natijasini qisqa o'zbekcha matn hisobotiga aylantiradi."""


def build(now, tz_name, trend_items, result, warnings, sample=False, post_status=None):
    from zoneinfo import ZoneInfo

    local = now.astimezone(ZoneInfo(tz_name))
    lines = [f"Kunlik Instagram hisobot: {local.strftime('%d.%m.%Y')}"]
    if sample:
        lines.append("(NAMUNA ma'lumot: haqiqiy emas, faqat sinov uchun)")
    lines.append("")

    if post_status:
        lines.append(f"Joylash: {post_status}")
        lines.append("")

    lines.append("Trend qidiruvlar (O'zbekiston):")
    if trend_items:
        for item in trend_items[:8]:
            traffic = f" ({item['traffic']})" if item.get("traffic") else ""
            lines.append(f"- {item['title']}{traffic}")
    else:
        lines.append("- ma'lumot yo'q")
    lines.append("")

    lines.append(
        f"Tahlil: {result['accounts']} akkaunt, {result['posts_analyzed']} post."
    )
    if result["accounts"] and not result["posts_analyzed"]:
        lines.append("Hali tahlil qilinadigan post yo'q (akkauntda postlar paydo bo'lgach to'ladi).")

    shared = result["shared_topics"]
    if shared:
        lines.append("")
        lines.append("Bir necha blogger tilga olgan mavzular (oxirgi 48 soat):")
        for item in shared[:6]:
            names = ", ".join("@" + a for a in item["accounts"][:4])
            lines.append(f"- {item['word']}: {names}")

    if result["best_hours"]:
        lines.append("")
        lines.append("Eng yaxshi joylash soatlari (Toshkent vaqti, engagement bo'yicha):")
        for item in result["best_hours"]:
            lines.append(
                f"- {item['hour']:02d}:00 (o'rtacha {item['avg_engagement']}%, {item['posts']} post)"
            )

    if result["top_hashtags"]:
        lines.append("")
        lines.append("Ko'p ishlatilgan teglar: " + ", ".join(f"#{t}" for t, _ in result["top_hashtags"][:8]))
    if result["top_words"]:
        lines.append("Ko'p ishlatilgan so'zlar: " + ", ".join(w for w, _ in result["top_words"][:8]))
    if result["posts_analyzed"]:
        lines.append(
            f"O'rtacha caption: {result['avg_caption_length']} belgi, {result['avg_emojis']} emoji."
        )

    if result["top_recent_posts"]:
        lines.append("")
        lines.append("Oxirgi 48 soatning eng kuchli postlari:")
        for post in result["top_recent_posts"][:3]:
            lines.append(f"- @{post['username']} {post['time']} ({post['engagement']}%): {post['caption']}")

    if warnings:
        lines.append("")
        lines.append("Ogohlantirishlar:")
        for warning in warnings[:8]:
            lines.append(f"- {warning}")

    return "\n".join(lines)
