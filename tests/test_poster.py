import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import poster, windsor  # noqa: E402


class FakeClient:
    def __init__(self):
        self.calls = []

    def action(self, action, params):
        self.calls.append((action, params))
        return {"ok": True}


class PosterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "queue").mkdir()
        queue = [
            {"id": "p1", "type": "image", "url": "https://x.test/a.jpg", "caption": "salom"},
            {"id": "p2", "type": "reel", "url": "https://x.test/b.mp4", "date": "2026-10-25"},
        ]
        (self.root / "queue" / "posts.json").write_text(json.dumps(queue), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_posts_once_per_day_and_respects_date(self):
        client = FakeClient()
        self.assertIn("joylandi", poster.run(client, self.root, "2026-10-22"))
        self.assertEqual(client.calls[0][0], "create_image_post")
        self.assertIn("allaqachon", poster.run(client, self.root, "2026-10-22"))
        # p2 ning sanasi hali kelmagan
        self.assertIn("Navbatda post yo'q", poster.run(client, self.root, "2026-10-23"))
        self.assertIn("joylandi", poster.run(client, self.root, "2026-10-25"))
        self.assertEqual(client.calls[1][0], "create_video_post")

    def test_dry_run_does_not_post(self):
        client = FakeClient()
        self.assertIn("dry-run", poster.run(client, self.root, "2026-10-22", dry_run=True))
        self.assertEqual(client.calls, [])

    def test_validate(self):
        self.assertIsNotNone(poster.validate({"type": "carousel", "urls": ["a"]}))
        self.assertIsNone(poster.validate({"type": "image", "url": "https://x"}))

    def test_publish_mapping(self):
        client = FakeClient()
        windsor.publish(client, {"type": "story", "url": "https://x.test/v.mp4"})
        self.assertEqual(client.calls[0], ("create_story", {"video_url": "https://x.test/v.mp4"}))


if __name__ == "__main__":
    unittest.main()
