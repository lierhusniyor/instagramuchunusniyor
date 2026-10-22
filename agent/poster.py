"""Kunlik avtomatik joylash: queue/posts.json dan navbatdagi postni Instagram'ga qo'yadi.

queue/posts.json (ro'yxat), har element:
  {"id": "p1", "type": "image|carousel|reel|story", "url": "https://...",
   "urls": ["https://...", "https://..."],   # faqat carousel uchun (2-10 ta)
   "caption": "matn #teg", "date": "2026-10-23"}  # date ixtiyoriy: shu kundan oldin joylanmaydi

Joylangan postlar state/posted.json ga yoziladi (bir kunda 1 tadan ko'p joylamaydi).
Rasm/video havolasi OCHIQ (public) bo'lishi shart.
"""
import json
from pathlib import Path

from . import windsor

TYPES = {"image", "carousel", "reel", "story"}


def _load(path, default):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def validate(item):
    if item.get("type") not in TYPES:
        return f"type noto'g'ri: {item.get('type')}"
    if item["type"] == "carousel":
        urls = item.get("urls") or []
        if not 2 <= len(urls) <= 10:
            return "carousel uchun 2-10 ta 'urls' kerak"
    elif not item.get("url"):
        return "'url' yo'q"
    return None


def next_item(queue, posted, today):
    done = {p["id"] for p in posted}
    for item in queue:
        if item.get("id") in done:
            continue
        if item.get("date") and item["date"] > today:
            continue
        return item
    return None


def run(client, root, today, dry_run=False):
    """Matn qaytaradi (Telegram hisobotiga qo'shiladi)."""
    root = Path(root)
    queue = _load(root / "queue" / "posts.json", [])
    state_path = root / "state" / "posted.json"
    posted = _load(state_path, [])

    if any(p.get("date") == today for p in posted):
        return "Bugun post allaqachon joylangan."
    item = next_item(queue, posted, today)
    if not item:
        return "Navbatda post yo'q (queue/posts.json bo'sh yoki hammasi joylangan)."
    problem = validate(item)
    if problem:
        return f"Post '{item.get('id')}' o'tkazib yuborildi: {problem}"
    if dry_run:
        return f"[dry-run] Joylanadi: {item['id']} ({item['type']})"

    try:
        result = windsor.publish(client, item)
    except Exception as exc:  # noqa: BLE001
        return f"Post '{item['id']}' joylanmadi: {exc}"

    posted.append({"id": item["id"], "date": today, "type": item["type"], "result": result})
    state_path.parent.mkdir(exist_ok=True)
    state_path.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Post joylandi: {item['id']} ({item['type']})."
