"""ISL public CLI; standard-library only, with no implicit network operations."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .core import SpectrumError, SpectrumRecord, exact_axis_filter, intersection, union, blend, midpoint_cosine
from .language import ISLError, run_file
from .adapter import (AdapterError, EncoderInfo, load_requests, load_predictions,
                      validate_pair, abstention_template)
from .evaluation import load_heldout, evaluate


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
    template = sub.add_parser("adapter-template", help="write abstaining JSON placeholders for an external encoder")
    template.add_argument("requests")
    template.add_argument("--out", required=True, help="new file only; never overwrites existing files")
    template.add_argument("--encoder-name", required=True)
    template.add_argument("--encoder-version", required=True)
    template.add_argument("--run-id", required=True)
    check = sub.add_parser("adapter-check", help="fail-closed validation of offline encoder outputs")
    check.add_argument("requests")
    check.add_argument("predictions")
    assessment = sub.add_parser("evaluate", help="held-out annotated point-score diagnostics")
    assessment.add_argument("requests")
    assessment.add_argument("predictions")
    assessment.add_argument("labels")
    args = parser.parse_args(argv)
    try:
        if args.command == "adapter-template":
            requests = load_requests(args.requests)
            info = EncoderInfo.from_json({"name": args.encoder_name,
                                          "version": args.encoder_version,
                                          "run_id": args.run_id,
                                          "source": "offline-template"})
            template_data = abstention_template(requests, info)
            with Path(args.out).open("x", encoding="utf-8") as handle:
                json.dump(template_data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            result = {"status": "created", "path": str(args.out), "requests": len(requests)}
        elif args.command in ("adapter-check", "evaluate"):
            requests = load_requests(args.requests)
            predictions = load_predictions(args.predictions)
            validate_pair(requests, predictions)
            if args.command == "adapter-check":
                result = {"status": "valid", "profile": "isl-encoder-adapter/0.2",
                          "requests": len(requests),
                          "predicted": sum(p.abstain_reason is None for p in predictions),
                          "abstained": sum(p.abstain_reason is not None for p in predictions)}
            else:
                annotation_protocol, labels = load_heldout(args.labels)
                result = evaluate(requests, predictions, labels, annotation_protocol)
        elif args.command in ("run", "check"):
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
    except (ISLError, SpectrumError, AdapterError, ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
        print(f"ISL error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
