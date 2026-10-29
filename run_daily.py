#!/usr/bin/env python3
"""Kunlik ish: python3 run_daily.py [--sample] [--dry-run] [--post]

--post     navbatdagi postni Instagram'ga joylaydi (Windsor orqali)
--dry-run  hech narsa yubormaydi/joylamaydi, faqat chop etadi
--sample   namuna ma'lumot bilan sinash (tarmoqsiz)
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from agent import analyze, notify, poster, report, trends, windsor

ROOT = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="namuna ma'lumot bilan sinash")
    parser.add_argument("--dry-run", action="store_true", help="yubormasdan chop etish")
    parser.add_argument("--post", action="store_true", help="navbatdagi postni joylash")
    args = parser.parse_args()

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    warnings = []
    post_status = None

    if args.sample:
        sample = json.loads((ROOT / "tests" / "sample_data.json").read_text(encoding="utf-8"))
        accounts = sample["accounts"]
        trend_items = sample["trends"]
        now = datetime.fromisoformat(sample["now"])
    else:
        now = datetime.now(timezone.utc)
        client = None
        api_key = os.environ.get("WINDSOR_API_KEY")
        if api_key:
            try:
                client = windsor.WindsorMCP(api_key)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Windsor'ga ulanilmadi: {exc}")
        else:
            warnings.append("WINDSOR_API_KEY yo'q: Instagram tahlili va joylash o'tkazib yuborildi.")

        if client and args.post:
            today = now.astimezone(ZoneInfo(config["timezone"])).date().isoformat()
            post_status = poster.run(client, ROOT, today, dry_run=args.dry_run)

        accounts = []
        if client:
            try:
                accounts = windsor.collect(client, config["lookback_days"])
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Instagram ma'lumoti olinmadi: {exc}")
        try:
            trend_items = trends.collect(config.get("trends_geo", "UZ"))
        except Exception as exc:  # noqa: BLE001
            trend_items = []
            warnings.append(f"Google Trends olinmadi: {exc}")

    result = analyze.analyze(accounts, config["timezone"], config["lookback_days"], now)
    text = report.build(
        now, config["timezone"], trend_items, result, warnings,
        sample=args.sample, post_status=post_status,
    )

    if not args.sample:
        data_dir = ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        snapshot = {"date": now.date().isoformat(), "trends": trend_items, "analysis": result}
        (data_dir / f"{now.date().isoformat()}.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if not args.sample:
        state = ROOT / "state"
        state.mkdir(exist_ok=True)
        (state / "last_run.txt").write_text(
            f"{now.isoformat()}\njoylash: {post_status}\nogohlantirishlar: {warnings}\n", encoding="utf-8"
        )

    if args.sample or args.dry_run:
        print(text)
    else:
        notify.send(text)


if __name__ == "__main__":
    main()
