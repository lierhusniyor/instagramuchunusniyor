#!/usr/bin/env python3
"""Sinov uchun SUN'IY ma'lumot yaratadi (haqiqiy blogger ma'lumoti emas)."""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(7)
NOW = datetime(2026, 10, 21, 15, 0, tzinfo=timezone.utc)
CAPTIONS = [
    "Yangi klip chiqdi 🔥 #premyera #uzbekistan",
    "Kunlik hayot va kulgi 😂 #mem #kulgi",
    "Sahnadan lavhalar #konsert #sahna",
    "Reaksiya video: yangi trend #reaksiya #trend",
    "Sizga savol: qaysi biri yoqdi? #savol #fikr",
]
SHARED = "Konsert haqida fikrim: juda zo'r bo'ldi #konsert #fikr"

accounts = []
for name, followers in [("demo_blogger_a", 2_000_000), ("demo_blogger_b", 800_000), ("demo_blogger_c", 300_000)]:
    posts = []
    for day in range(10):
        for _ in range(random.choice([1, 1, 2])):
            ts = NOW - timedelta(days=day + 1, hours=random.randint(0, 10))
            ts = ts.replace(hour=random.choice([8, 12, 15, 16, 17]))  # UTC; Toshkent = +5
            likes = int(followers * random.uniform(0.005, 0.03))
            posts.append(
                {
                    "caption": random.choice(CAPTIONS),
                    "like_count": likes,
                    "comments_count": int(likes * random.uniform(0.01, 0.05)),
                    "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S+0000"),
                    "permalink": f"https://example.com/{name}/{day}",
                }
            )
    posts.append(
        {
            "caption": SHARED,
            "like_count": int(followers * 0.04),
            "comments_count": int(followers * 0.002),
            "timestamp": (NOW - timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%S+0000"),
            "permalink": f"https://example.com/{name}/shared",
        }
    )
    accounts.append({"username": name, "followers": followers, "posts": posts})

data = {
    "_synthetic": True,
    "now": NOW.isoformat(),
    "trends": [
        {"title": "namuna trend 1", "traffic": "200+"},
        {"title": "namuna trend 2", "traffic": "100+"},
    ],
    "accounts": accounts,
}
out = Path(__file__).parent / "sample_data.json"
out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Yozildi: {out}")
