"""ISL P2: model-neutral, offline semantic-score interchange contracts.

External encoders may supply predictions, but this module does not load a model,
make network calls, infer objective meaning, or grant predictions proof status.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Protocol

from .core import Interval, SpectrumError

REQUEST_PROFILE = "isl-encode-requests/0.2"
PREDICTION_PROFILE = "isl-encode-predictions/0.2"
_HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
_AXIS = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


class AdapterError(ValueError):
    """Invalid encoder-interface input or output; fail closed."""


def _fields(value: object, required: set[str], where: str) -> dict:
    if not isinstance(value, dict) or set(value) != required:
        raise AdapterError(f"{where}: required fields {sorted(required)}")
    return value


def _name(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise AdapterError(f"{where}: expected nonempty bounded string")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise AdapterError(f"{where}: invalid UTF-8") from exc
    return value


@dataclass(frozen=True)
class EncodeRequest:
    item_id: str
    text: str
    context: str
    context_group: str
    axes: tuple[str, ...]

    @classmethod
    def from_json(cls, raw: object) -> "EncodeRequest":
        d = _fields(raw, {"item_id", "text", "context", "context_group", "axes"}, "request")
        item_id = _name(d["item_id"], "item_id")
        text = _name(d["text"], "text")
        context = _name(d["context"], "context")
        group = _name(d["context_group"], "context_group")
        axes = d["axes"]
        if (not isinstance(axes, list) or not 1 <= len(axes) <= 256
                or any(not isinstance(a, str) or not _AXIS.fullmatch(a) for a in axes)
                or len(set(axes)) != len(axes)):
            raise AdapterError("request axes must be 1..256 unique identifier strings")
        return cls(item_id, text, context, group, tuple(axes))

    def canonical_fields(self) -> dict:
        return {"axes": list(self.axes), "context": self.context,
                "context_group": self.context_group, "text": self.text}

    @property
    def input_sha256(self) -> str:
        """Fingerprint for binding, not anonymity, authentication, or secrecy."""
        canonical = json.dumps(self.canonical_fields(), ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        return sha256(b"ISL-P2-INPUT\0" + canonical).hexdigest()


@dataclass(frozen=True)
class EncoderInfo:
    name: str
    version: str
    run_id: str
    source: str

    @classmethod
    def from_json(cls, raw: object) -> "EncoderInfo":
        d = _fields(raw, {"name", "version", "run_id", "source"}, "encoder")
        return cls(*(_name(d[k], f"encoder.{k}") for k in ("name", "version", "run_id", "source")))

    def to_json(self) -> dict:
        return {"name": self.name, "version": self.version, "run_id": self.run_id, "source": self.source}


@dataclass(frozen=True)
class EncodePrediction:
    item_id: str
    input_sha256: str
    encoder: EncoderInfo
    axes: dict[str, Interval]
    abstain_reason: str | None

    @classmethod
    def from_json(cls, raw: object) -> "EncodePrediction":
        d = _fields(raw, {"item_id", "input_sha256", "encoder", "axes", "abstain_reason"}, "prediction")
        item_id = _name(d["item_id"], "prediction.item_id")
        digest = d["input_sha256"]
        if not isinstance(digest, str) or not _HEX_SHA.fullmatch(digest):
            raise AdapterError("prediction.input_sha256 must be lowercase SHA-256 hex")
        encoder = EncoderInfo.from_json(d["encoder"])
        reason = d["abstain_reason"]
        if reason is not None:
            reason = _name(reason, "abstain_reason")
        if not isinstance(d["axes"], dict):
            raise AdapterError("prediction axes must be an object")
        try:
            axes = {k: Interval.from_json(v) for k, v in d["axes"].items()}
        except (SpectrumError, TypeError) as exc:
            raise AdapterError(f"prediction invalid interval: {exc}") from exc
        if any(not isinstance(k, str) or not _AXIS.fullmatch(k) for k in axes):
            raise AdapterError("prediction has invalid axis identifier")
        if reason is not None and axes:
            raise AdapterError("abstaining predictions cannot include axes")
        if reason is None and not axes:
            raise AdapterError("non-abstaining predictions must include axes")
        return cls(item_id, digest, encoder, axes, reason)

    def to_json(self) -> dict:
        return {"item_id": self.item_id, "input_sha256": self.input_sha256,
                "encoder": self.encoder.to_json(),
                "axes": {k: v.to_json() for k, v in sorted(self.axes.items())},
                "abstain_reason": self.abstain_reason}


class SpectrumEncoder(Protocol):
    """Implement this in an external model/tool adapter; no loading is implicit."""

    def encode(self, request: EncodeRequest) -> EncodePrediction:
        ...


def load_requests(path: str | Path) -> list[EncodeRequest]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    d = _fields(obj, {"profile", "items"}, "requests bundle")
    if d["profile"] != REQUEST_PROFILE or not isinstance(d["items"], list) or not d["items"]:
        raise AdapterError("wrong requests profile or empty items")
    items = [EncodeRequest.from_json(row) for row in d["items"]]
    if len({r.item_id for r in items}) != len(items):
        raise AdapterError("duplicate request item_id")
    return items


def load_predictions(path: str | Path) -> list[EncodePrediction]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    d = _fields(obj, {"profile", "predictions"}, "predictions bundle")
    if d["profile"] != PREDICTION_PROFILE or not isinstance(d["predictions"], list) or not d["predictions"]:
        raise AdapterError("wrong predictions profile or empty predictions")
    predictions = [EncodePrediction.from_json(row) for row in d["predictions"]]
    if len({p.item_id for p in predictions}) != len(predictions):
        raise AdapterError("duplicate prediction item_id")
    return predictions


def validate_pair(requests: list[EncodeRequest], predictions: list[EncodePrediction]) -> None:
    request_map = {r.item_id: r for r in requests}
    prediction_map = {p.item_id: p for p in predictions}
    if len(request_map) != len(requests) or len(prediction_map) != len(predictions):
        raise AdapterError("duplicate item_id")
    if request_map.keys() != prediction_map.keys():
        raise AdapterError("predictions must match every request ID exactly (no extras or omissions)")
    for item_id, r in request_map.items():
        p = prediction_map[item_id]
        if p.input_sha256 != r.input_sha256:
            raise AdapterError(f"{item_id}: input digest mismatch (text/context/axes changed)")
        if p.abstain_reason is None and set(p.axes) != set(r.axes):
            raise AdapterError(f"{item_id}: predicted axes must match request exactly")


class FixtureReplayEncoder:
    """Offline demonstration of a provider plug-in, not a learned model."""

    def __init__(self, requests: list[EncodeRequest], predictions: list[EncodePrediction]):
        validate_pair(requests, predictions)
        self._predictions = {p.item_id: p for p in predictions}

    def encode(self, request: EncodeRequest) -> EncodePrediction:
        prediction = self._predictions.get(request.item_id)
        if prediction is None or prediction.input_sha256 != request.input_sha256:
            raise AdapterError("fixture replay input not found or changed")
        return prediction


def abstention_template(requests: list[EncodeRequest], encoder: EncoderInfo) -> dict:
    """Produces a syntactically valid abstaining placeholder; never invents scores."""
    return {"profile": PREDICTION_PROFILE, "predictions": [
        EncodePrediction(r.item_id, r.input_sha256, encoder, {},
                         "not yet encoded").to_json() for r in requests]}
