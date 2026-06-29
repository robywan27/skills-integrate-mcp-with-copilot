#!/usr/bin/env python3
"""
Minimal ETL script to ingest, normalize and aggregate student activity records.

Usage:
  python src/ingest.py --input src/sample_activities.json --output src/aggregated.json

The script expects a JSON array of activity records. Supported input fields (best-effort):
- student_id or mssv or id
- student_name or name
- activity (string)
- points (number)

Output: JSON object keyed by student_id with aggregated totals and activity lists.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def normalize_record(rec: dict):
    # best-effort field mappings
    sid = rec.get("student_id") or rec.get("mssv") or rec.get("id")
    name = rec.get("student_name") or rec.get("name") or ""
    activity = rec.get("activity") or rec.get("activity_name") or rec.get("title") or ""
    try:
        points = float(rec.get("points", 0) or 0)
    except Exception:
        points = 0
    if sid is None:
        # try to infer from nested structures
        sid = rec.get("student", {}).get("id") if isinstance(rec.get("student"), dict) else None
    if sid is None:
        return None
    return {
        "student_id": str(sid),
        "student_name": name,
        "activity": activity,
        "points": points,
    }


def aggregate(records):
    out = {}
    agg = defaultdict(lambda: {"student_name": "", "total_points": 0.0, "activity_count": 0, "activities": []})
    for r in records:
        nr = normalize_record(r)
        if not nr:
            continue
        sid = nr["student_id"]
        row = agg[sid]
        if nr.get("student_name"):
            row["student_name"] = nr["student_name"]
        row["total_points"] += nr.get("points", 0)
        row["activity_count"] += 1
        row["activities"].append({"activity": nr.get("activity"), "points": nr.get("points")})

    # convert defaultdict to plain dict
    for sid, data in agg.items():
        out[sid] = data
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="src/sample_activities.json")
    parser.add_argument("--output", "-o", default="src/aggregated.json")
    args = parser.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file {inp} not found")
        raise SystemExit(1)

    records = json.loads(inp.read_text())
    if not isinstance(records, list):
        print("Input should be a JSON array of activity records")
        raise SystemExit(1)

    aggregated = aggregate(records)

    outp = Path(args.output)
    outp.write_text(json.dumps(aggregated, indent=2, ensure_ascii=False))
    print(f"Wrote aggregated output to {outp}")


if __name__ == "__main__":
    main()
