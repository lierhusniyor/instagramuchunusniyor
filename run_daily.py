#!/usr/bin/env python3
"""Kunlik tahlil: python3 run_daily.py [--sample] [--dry-run]"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from agent import analyze, graph_api, notify, report, trends

ROOT = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="namuna ma'lumot bilan sinash")
    parser.add_argument("--dry-run", action="store_true", help="yubormasdan chop etish")
    args = parser.parse_args()

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    warnings = []

    if args.sample:
        sample = json.loads((ROOT / "tests" / "sample_data.json").read_text(encoding="utf-8"))
        accounts = sample["accounts"]
        trend_items = sample["trends"]
        now = datetime.fromisoformat(sample["now"])
    else:
        now = datetime.now(timezone.utc)
        accounts, account_warnings = graph_api.collect(config)
        warnings += account_warnings
        try:
            trend_items = trends.collect(config.get("trends_geo", "UZ"))
        except Exception as exc:  # noqa: BLE001
            trend_items = []
            warnings.append(f"Google Trends olinmadi: {exc}")

    result = analyze.analyze(accounts, config["timezone"], config["lookback_days"], now)
    text = report.build(now, config["timezone"], trend_items, result, warnings, sample=args.sample)

    if not args.sample:
        data_dir = ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        snapshot = {"date": now.date().isoformat(), "trends": trend_items, "analysis": result}
        (data_dir / f"{now.date().isoformat()}.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if args.sample or args.dry_run:
        print(text)
    else:
        notify.send(text)


if __name__ == "__main__":
    main()
