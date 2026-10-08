"""Minimal, non-neural and dependency-free interval-spectrum operations.

This reference example intentionally makes no claim to semantic understanding.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Mapping, Any

PROFILE = "spectrum-public/0.1"

class SpectrumError(ValueError):
    """A record or operation is outside the v0.1 profile."""

@dataclass(frozen=True, order=True)
class Interval:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if (isinstance(self.lower, bool) or isinstance(self.upper, bool)
            or not isinstance(self.lower, (int, float))
            or not isinstance(self.upper, (int, float))
            or not isfinite(self.lower) or not isfinite(self.upper)
            or not (0 <= self.lower <= self.upper <= 1)):
            raise SpectrumError("interval requires finite 0 <= lower <= upper <= 1")

    @property
    def midpoint(self) -> float:
        return (self.lower + self.upper) / 2

    def to_json(self) -> dict:
        return {"lower": self.lower, "upper": self.upper}

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> 'Interval':
        if not isinstance(value, dict) or set(value) != {"lower", "upper"}:
            raise SpectrumError("interval must contain exactly lower and upper")
        return cls(value["lower"], value["upper"])

@dataclass(frozen=True)
class SpectrumRecord:
    record_id: str
    text: str
    context: str
    provenance: str
    axes: Mapping[str, Interval]

    @classmethod
    def from_json(cls, raw: dict) -> 'SpectrumRecord':
        if not isinstance(raw, dict):
            raise SpectrumError("record must be object")
        required = {"profile", "record_id", "text", "context", "provenance", "axes"}
        if set(raw) != required or raw["profile"] != PROFILE:
            raise SpectrumError("wrong profile or record fields")
        for key in ("record_id", "text", "context", "provenance"):
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise SpectrumError(f"{key} must be nonempty string")
        if not isinstance(raw["axes"], dict) or not raw["axes"]:
            raise SpectrumError("axes must be a nonempty object")
        axes = {}
        for k, v in raw["axes"].items():
            if not isinstance(k, str) or not k.strip():
                raise SpectrumError("axis name must be nonempty")
            axes[k] = Interval.from_json(v)
        return cls(raw["record_id"], raw["text"], raw["context"], raw["provenance"], axes)

def intersection(a: Interval, b: Interval) -> Interval | None:
    lo, hi = max(a.lower, b.lower), min(a.upper, b.upper)
    return Interval(lo, hi) if lo <= hi else None

def union(a: Interval, b: Interval) -> list[Interval]:
    """Exact union, including two disjoint intervals when necessary."""
    first, second = sorted((a, b))
    if first.upper < second.lower:
        return [first, second]
    return [Interval(first.lower, max(first.upper, second.upper))]

def blend(a: Interval, b: Interval, alpha: float) -> Interval:
    """Numerical interpolation only; no logical entailment is claimed."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not isfinite(alpha) or not 0 <= alpha <= 1:
        raise SpectrumError("alpha must be finite within [0, 1]")
    return Interval(alpha*a.lower+(1-alpha)*b.lower,
                    alpha*a.upper+(1-alpha)*b.upper)

def midpoint_cosine(a: SpectrumRecord, b: SpectrumRecord) -> float:
    """Heuristic similarity. Identical named axes are required."""
    if set(a.axes) != set(b.axes):
        raise SpectrumError("axis sets differ; explicit mapping is required")
    keys = sorted(a.axes)
    x, y = [a.axes[k].midpoint for k in keys], [b.axes[k].midpoint for k in keys]
    d = sqrt(sum(z*z for z in x) * sum(z*z for z in y))
    if not d:
        raise SpectrumError("zero vector has undefined cosine similarity")
    return sum(u*v for u,v in zip(x,y)) / d

def exact_axis_filter(records: list[SpectrumRecord], axis: str, minimum_lower: float) -> list[SpectrumRecord]:
    if not isinstance(minimum_lower, (int, float)) or isinstance(minimum_lower, bool) or not isfinite(minimum_lower) or not 0 <= minimum_lower <= 1:
        raise SpectrumError("minimum_lower out of bounds")
    return [r for r in records if axis in r.axes and r.axes[axis].lower >= minimum_lower]
