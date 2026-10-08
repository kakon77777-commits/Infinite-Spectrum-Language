"""ISL P2 held-out point-label diagnostics; no calibrated probabilities claimed."""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path

from .adapter import AdapterError, EncodeRequest, EncodePrediction, validate_pair, _fields, _name

EVALUATION_PROFILE = "isl-evaluation/0.2"


@dataclass(frozen=True)
class HeldoutLabel:
    item_id: str
    values: dict[str, float]
    annotation_source: str

    @classmethod
    def from_json(cls, raw: object) -> "HeldoutLabel":
        d = _fields(raw, {"item_id", "values", "annotation_source"}, "label")
        item_id = _name(d["item_id"], "label.item_id")
        source = _name(d["annotation_source"], "label.annotation_source")
        values = d["values"]
        if not isinstance(values, dict) or not values:
            raise AdapterError("label.values must be nonempty object")
        for axis, v in values.items():
            if not isinstance(axis, str) or isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or not 0 <= v <= 1:
                raise AdapterError("label axis point must be finite within [0,1]")
        return cls(item_id, values, source)


def load_heldout(path: str | Path) -> tuple[str, list[HeldoutLabel]]:
    d = _fields(json.loads(Path(path).read_text(encoding="utf-8")),
                {"profile", "split", "annotation_protocol", "labels"}, "held-out bundle")
    if d["profile"] != EVALUATION_PROFILE or d["split"] != "heldout":
        raise AdapterError("evaluation requires explicit 'heldout' profile/split")
    protocol = _name(d["annotation_protocol"], "annotation_protocol")
    if not isinstance(d["labels"], list) or not d["labels"]:
        raise AdapterError("held-out labels must be nonempty list")
    labels = [HeldoutLabel.from_json(row) for row in d["labels"]]
    if len({x.item_id for x in labels}) != len(labels):
        raise AdapterError("duplicate held-out label item_id")
    return protocol, labels


def _summarize(rows: list[tuple[float, float, float]]) -> dict:
    """Rows are (absolute midpoint error, point-in-interval 0/1, width)."""
    if not rows:
        return {"count": 0, "midpoint_mae": None, "point_coverage": None, "mean_interval_width": None}
    n = len(rows)
    return {"count": n, "midpoint_mae": sum(x[0] for x in rows) / n,
            "point_coverage": sum(x[1] for x in rows) / n,
            "mean_interval_width": sum(x[2] for x in rows) / n}


def evaluate(requests: list[EncodeRequest], predictions: list[EncodePrediction],
             labels: list[HeldoutLabel], annotation_protocol: str) -> dict:
    validate_pair(requests, predictions)
    req_map = {r.item_id: r for r in requests}
    pred_map = {p.item_id: p for p in predictions}
    label_map = {x.item_id: x for x in labels}
    if len(label_map) != len(labels) or req_map.keys() != label_map.keys():
        raise AdapterError("held-out label IDs must exactly match request IDs")
    seen_fingerprints: set[str] = set()
    for r in requests:
        if r.input_sha256 in seen_fingerprints:
            raise AdapterError("duplicate input fingerprint in held-out evaluation")
        seen_fingerprints.add(r.input_sha256)
        if set(r.axes) != set(label_map[r.item_id].values):
            raise AdapterError(f"{r.item_id}: label axes do not match request")
    by_group: dict[str, list[tuple[float, float, float]]] = {}
    by_axis: dict[str, list[tuple[float, float, float]]] = {}
    scored: list[tuple[float, float, float]] = []
    abstentions: dict[str, int] = {}
    for r in requests:
        p = pred_map[r.item_id]
        if p.abstain_reason is not None:
            abstentions[p.abstain_reason] = abstentions.get(p.abstain_reason, 0) + 1
            continue
        for axis in r.axes:
            interval = p.axes[axis]
            label = label_map[r.item_id].values[axis]
            row = (abs(interval.midpoint - label), float(interval.lower <= label <= interval.upper),
                   interval.upper - interval.lower)
            scored.append(row)
            by_group.setdefault(r.context_group, []).append(row)
            by_axis.setdefault(axis, []).append(row)
    model_set = sorted({(p.encoder.name, p.encoder.version, p.encoder.run_id, p.encoder.source) for p in predictions})
    if len(model_set) != 1:
        raise AdapterError("one evaluation may contain only one encoder/run; compare runs separately")
    model = predictions[0].encoder
    return {
        "profile": "isl-evaluation-report/0.2",
        "annotation_protocol": annotation_protocol,
        "encoder": model.to_json(),
        "request_count": len(requests),
        "scored_request_count": len(requests) - sum(abstentions.values()),
        "abstained_count": sum(abstentions.values()),
        "abstention_reasons": dict(sorted(abstentions.items())),
        "scored_axis_points": len(scored),
        "overall": _summarize(scored),
        "by_context_group": {k: _summarize(v) for k, v in sorted(by_group.items())},
        "by_axis": {k: _summarize(v) for k, v in sorted(by_axis.items())},
        "limitations": [
            "Scores compare to declared point annotations, not verified semantic truth.",
            "Point coverage and interval width are diagnostics, NOT probability calibration.",
            "Independent annotation, leakage prevention, and real context shift must be audited externally.",
            "Abstentions are excluded from scored-point metrics and counted separately."
        ],
    }
