"""ISL P1 CLI; standard-library only, with no implicit network operations."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .core import SpectrumError, SpectrumRecord, exact_axis_filter, intersection, union, blend, midpoint_cosine
from .language import ISLError, run_file


def load(path: str) -> list[SpectrumRecord]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expected list of records")
    records = [SpectrumRecord.from_json(row) for row in data]
    ids = [r.record_id for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate record_id")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="isl", description="Public, dependency-free bounded spectrum language")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "check", "validate", "query", "demo"):
        p = sub.add_parser(command)
        p.add_argument("path")
        if command == "query":
            p.add_argument("--axis", default="joy")
            p.add_argument("--lower-at-least", type=float, default=0.7)
    args = parser.parse_args(argv)
    try:
        if args.command in ("run", "check"):
            result = run_file(args.path)
            if args.command == "check":
                result = {"status": "valid", "profile": result["profile"], "axes": result["axes"], "records": result["records"]}
        else:
            records = load(args.path)
            if args.command == "validate":
                result = {"status": "valid", "records": len(records)}
            elif args.command == "query":
                result = [{"record_id": row.record_id, "text": row.text} for row in exact_axis_filter(records, args.axis, args.lower_at_least)]
            else:
                if len(records) < 2:
                    raise ValueError("need at least two records")
                a, b = records[:2]
                if set(a.axes) != set(b.axes):
                    raise SpectrumError("records need identical axis sets")
                axis = sorted(a.axes)[0]
                x, y = a.axes[axis], b.axes[axis]
                cross = intersection(x, y)
                result = {
                    "axis": axis,
                    "intersection": cross.to_json() if cross is not None else None,
                    "union": [interval.to_json() for interval in union(x, y)],
                    "blend_half": blend(x, y, 0.5).to_json(),
                    "cosine_midpoint_heuristic": midpoint_cosine(a, b),
                }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ISLError, SpectrumError, ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
        print(f"ISL error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
