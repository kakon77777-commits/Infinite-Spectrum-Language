"""Explicit P2 -> P3 projection. This does not certify predicted semantics."""
from __future__ import annotations

from .adapter import EncodeRequest, EncodePrediction, validate_pair
from .core import PROFILE, SpectrumRecord
from .retrieval import RetrievalError


def project_predictions(requests: list[EncodeRequest], predictions: list[EncodePrediction]) -> tuple[list[dict], dict]:
    validate_pair(requests, predictions)
    by_id = {p.item_id: p for p in predictions}
    signature = {(p.encoder.name, p.encoder.version, p.encoder.run_id, p.encoder.source) for p in predictions}
    if len(signature) != 1:
        raise RetrievalError("P2->P3 projection refuses mixed encoder provenance: split into separate corpora")
    axis_sets = {tuple(r.axes) for r in requests}
    if len(axis_sets) != 1:
        raise RetrievalError("P2->P3 projection requires one declared axis profile")
    records: list[dict] = []
    for request in requests:
        prediction = by_id[request.item_id]
        if prediction.abstain_reason is not None:
            continue
        provenance = (f"external P2 score prediction; encoder={prediction.encoder.name}; "
                      f"version={prediction.encoder.version}; run={prediction.encoder.run_id}; "
                      f"source={prediction.encoder.source}; "
                      f"group={request.context_group}; input_sha256={request.input_sha256}; "
                      "not verified semantic truth")
        records.append({"profile": PROFILE, "record_id": request.item_id,
                        "text": request.text, "context": request.context,
                        "provenance": provenance,
                        "axes": {axis: prediction.axes[axis].to_json() for axis in request.axes}})
    return records, {"profile": "isl-p2-corpus-projection/0.3", "requests": len(requests),
                     "materialized": len(records), "abstained": len(requests) - len(records),
                     "boundary": "P2 predictions are external numeric annotations, not ground truth"}
