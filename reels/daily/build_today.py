#!/usr/bin/env python3
"""Kunlik: navbatdagi ssenariydan video yasaydi va queue/posts.json ga bugungi reel sifatida qo'shadi.

GitHub Actions (daily.yml) chaqiradi. Ssenariylar tugasa, boshidan aylanadi (id ga '-2', '-3' qo'shiladi).
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import make_video  # noqa: E402

RAW = "https://raw.githubusercontent.com/lierhusniyor/instagramuchunusniyor/main/"


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    today = datetime.now(ZoneInfo(config["timezone"])).date().isoformat()
    qpath = ROOT / "queue" / "posts.json"
    queue = json.loads(qpath.read_text(encoding="utf-8")) if qpath.exists() else []
    if any(q.get("date") == today and q.get("auto") for q in queue):
        print("Bugungi video allaqachon navbatda.")
        return

    scripts = json.loads((HERE / "scripts.json").read_text(encoding="utf-8"))
    # Navbatda hali ishlatilmagan birinchi ssenariy (h001 -> h180). Hammasi tugasa, boshidan aylanadi.
    used = {q["id"] for q in queue if q.get("auto")}
    script, pid = None, None
    for rnd in range(1, 100):
        for s in scripts:
            cand = s["id"] if rnd == 1 else f"{s['id']}-{rnd}"
            if cand not in used:
                script, pid = s, cand
                break
        if script:
            break

    rel = f"reels/daily/out/{pid}.mp4"
    hero = {h["id"]: h for h in json.loads((HERE / "hero_scripts.json").read_text(encoding="utf-8"))}
    if script["id"] in hero:  # qahramonli (USTOZ) versiya bor bo'lsa, o'shani ishlat
        import hero_video
        script = dict(script, caption=hero[script["id"]]["caption"], tags=hero[script["id"]]["tags"])
        info = hero_video.render(hero[script["id"]], ROOT / rel)
    else:
        info = make_video.render(script, ROOT / rel)
    print(f"Video: {rel} {info}")

    caption = f"{script['caption']}\n\n{' '.join(script['tags'][:5])}"
    queue.append({"id": pid, "type": "reel", "url": RAW + rel, "caption": caption,
                  "date": today, "auto": True})
    qpath.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
