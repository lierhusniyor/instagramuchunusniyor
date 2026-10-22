import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.analyze import analyze, parse_ts  # noqa: E402

NOW = datetime(2026, 10, 21, 15, 0, tzinfo=timezone.utc)


def post(ts, caption, likes=100):
    return {"timestamp": ts, "caption": caption, "like_count": likes, "comments_count": 0}


class AnalyzeTests(unittest.TestCase):
    def test_parse_ts_variants(self):
        self.assertEqual(parse_ts("2026-10-20T10:00:00+0000").hour, 10)
        self.assertEqual(parse_ts("2026-10-20T10:00:00Z").hour, 10)
        self.assertEqual(parse_ts("2026-10-20T10:00:00+05:00").hour, 10)

    def test_parse_ts_naive_is_utc(self):
        self.assertEqual(parse_ts("2026-10-20 10:00:00").utcoffset().total_seconds(), 0)

    def test_shared_topic_and_hours(self):
        accounts = [
            {"username": "a", "followers": 1000, "posts": [
                post("2026-10-21T01:00:00+0000", "Konsert haqida #konsert", 50),
                post("2026-10-20T07:00:00+0000", "Boshqa post", 10),
                post("2026-10-19T07:00:00+0000", "Yana post", 12),
            ]},
            {"username": "b", "followers": 1000, "posts": [
                post("2026-10-21T02:00:00+0000", "Konsert juda zo'r", 40),
            ]},
        ]
        result = analyze(accounts, "Asia/Tashkent", 14, NOW)
        self.assertEqual(result["posts_analyzed"], 4)
        self.assertIn("konsert", [t["word"] for t in result["shared_topics"]])
        # 07:00 UTC = 12:00 Toshkent, 2 ta post
        self.assertEqual(dict(result["post_hours"])[12], 2)
        self.assertIn(("konsert", 1), result["top_hashtags"])

    def test_old_posts_ignored(self):
        accounts = [{"username": "a", "followers": 10, "posts": [post("2026-01-01T00:00:00+0000", "eski")]}]
        self.assertEqual(analyze(accounts, "Asia/Tashkent", 14, NOW)["posts_analyzed"], 0)


if __name__ == "__main__":
    unittest.main()
