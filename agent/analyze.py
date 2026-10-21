"""Postlarni tahlil qiladi: vaqt, so'z, teg va bir nechta blogger tilga olgan mavzular."""
import collections
import re
from datetime import timedelta
from datetime import datetime
from zoneinfo import ZoneInfo

WORD_RE = re.compile(r"[^\W\d_]{4,}", re.UNICODE)
HASH_RE = re.compile(r"#(\w+)", re.UNICODE)
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
STOP = {
    "bilan", "uchun", "lekin", "yoki", "bugun", "kecha", "ham", "siz", "biz", "ular",
    "bizning", "sizga", "mening", "sening", "uning", "bundan", "shunday", "juda",
    "haqida", "yangi", "chiqdi", "qaysi", "biri", "yoqdi", "kerak", "bo'ldi",
    "this", "that", "with", "from", "have", "your", "what",
    "что", "как", "это", "для", "при", "все", "если", "очень",
}


def parse_ts(ts):
    """Graph API '+0000' ko'rinishidagi vaqtni ham, 'Z' ni ham o'qiydi."""
    ts = ts.strip().replace("Z", "+00:00")
    match = re.search(r"([+-]\d{2})(\d{2})$", ts)
    if match:
        ts = ts[: match.start()] + f"{match.group(1)}:{match.group(2)}"
    return datetime.fromisoformat(ts)


def engagement(post, followers):
    total = (post.get("like_count") or 0) + (post.get("comments_count") or 0)
    return total / followers * 100 if followers else 0.0


def analyze(accounts, tz_name, lookback_days, now):
    tz = ZoneInfo(tz_name)
    since = now - timedelta(days=lookback_days)
    recent_since = now - timedelta(hours=48)

    hours = collections.Counter()
    hour_eng = collections.defaultdict(list)
    tags = collections.Counter()
    words = collections.Counter()
    caption_lens, emoji_counts = [], []
    recent_words = collections.defaultdict(set)
    top_recent = []
    n_posts = 0

    for acc in accounts:
        followers = acc.get("followers") or 0
        for post in acc.get("posts", []):
            try:
                ts = parse_ts(post["timestamp"])
            except (KeyError, ValueError):
                continue
            if ts < since or ts > now:
                continue
            n_posts += 1
            local = ts.astimezone(tz)
            eng = engagement(post, followers)
            hours[local.hour] += 1
            hour_eng[local.hour].append(eng)

            caption = post.get("caption") or ""
            for tag in HASH_RE.findall(caption):
                tags[tag.lower()] += 1
            caption_words = [w.lower() for w in WORD_RE.findall(HASH_RE.sub("", caption))]
            caption_words = [w for w in caption_words if w not in STOP]
            words.update(caption_words)
            caption_lens.append(len(caption))
            emoji_counts.append(len(EMOJI_RE.findall(caption)))

            if ts >= recent_since:
                for word in set(caption_words):
                    recent_words[word].add(acc["username"])
                top_recent.append(
                    {
                        "username": acc["username"],
                        "engagement": round(eng, 2),
                        "caption": caption[:120],
                        "permalink": post.get("permalink", ""),
                        "time": local.strftime("%d.%m %H:%M"),
                    }
                )

    best_hours = sorted(
        ((h, sum(v) / len(v), len(v)) for h, v in hour_eng.items() if len(v) >= 2),
        key=lambda item: -item[1],
    )[:3]
    shared = sorted(
        ((w, sorted(a)) for w, a in recent_words.items() if len(a) >= 2),
        key=lambda item: (-len(item[1]), item[0]),
    )[:10]
    top_recent.sort(key=lambda item: -item["engagement"])

    def avg(values):
        return round(sum(values) / len(values), 1) if values else 0

    return {
        "posts_analyzed": n_posts,
        "accounts": len(accounts),
        "post_hours": sorted(hours.items()),
        "best_hours": [
            {"hour": h, "avg_engagement": round(e, 2), "posts": n} for h, e, n in best_hours
        ],
        "top_hashtags": tags.most_common(10),
        "top_words": words.most_common(10),
        "shared_topics": [{"word": w, "accounts": a} for w, a in shared],
        "top_recent_posts": top_recent[:5],
        "avg_caption_length": avg(caption_lens),
        "avg_emojis": avg(emoji_counts),
    }
