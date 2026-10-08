"""ISL P3: deterministic, explicitly scoped numerical-spectra retrieval.

Candidate selection is replaceable and may miss true matches.  Final interval
predicates are evaluated against the validated source records, never against an
index approximation. Numerical similarity is not entailment or semantic truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from math import isfinite
from pathlib import Path
import re
from typing import Protocol, Sequence

from .core import SpectrumError, SpectrumRecord, midpoint_cosine

QUERY_PROFILE = "isl-retrieval-query/0.3"
RESULT_PROFILE = "isl-retrieval-results/0.3"
OUTPUT_PROFILE = "isl-controlled-output/0.3"
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


class RetrievalError(ValueError):
    """Invalid P3 query, corpus or candidate provider."""


def _exact_fields(value: object, fields: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise RetrievalError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _bounded_string(value: object, label: str, limit: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise RetrievalError(f"{label}: expected non-empty bounded string")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise RetrievalError(f"{label}: invalid UTF-8 text") from exc
    return value


@dataclass(frozen=True)
class Predicate:
    axis: str
    endpoint: str
    operator: str
    threshold: float

    @classmethod
    def from_json(cls, obj: object) -> "Predicate":
        d = _exact_fields(obj, {"axis", "endpoint", "operator", "threshold"}, "predicate")
        if not isinstance(d["axis"], str) or not _IDENTIFIER.fullmatch(d["axis"]):
            raise RetrievalError("predicate axis must be an identifier")
        if d["endpoint"] not in ("lower", "upper") or d["operator"] not in (">=", "<="):
            raise RetrievalError("predicate endpoint/operator unsupported")
        value = d["threshold"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0 <= value <= 1:
            raise RetrievalError("predicate threshold must be finite within [0,1]")
        return cls(d["axis"], d["endpoint"], d["operator"], value)

    def evaluate(self, record: SpectrumRecord) -> bool:
        observed = getattr(record.axes[self.axis], self.endpoint)
        return observed >= self.threshold if self.operator == ">=" else observed <= self.threshold


@dataclass(frozen=True)
class RetrievalQuery:
    context: str
    axes: tuple[str, ...]
    reference_id: str
    predicates: tuple[Predicate, ...]
    max_results: int
    exclude_reference: bool

    @classmethod
    def from_json(cls, obj: object) -> "RetrievalQuery":
        d = _exact_fields(obj, {"profile", "context", "axes", "reference_id", "predicates", "max_results", "exclude_reference"}, "query")
        if d["profile"] != QUERY_PROFILE:
            raise RetrievalError("unsupported retrieval query profile")
        context = _bounded_string(d["context"], "context")
        reference = _bounded_string(d["reference_id"], "reference_id", 256)
        axes = d["axes"]
        if (not isinstance(axes, list) or not 1 <= len(axes) <= 256
                or any(not isinstance(a, str) or not _IDENTIFIER.fullmatch(a) for a in axes)
                or len(set(axes)) != len(axes)):
            raise RetrievalError("axes must be 1..256 unique identifiers")
        predicates = d["predicates"]
        if not isinstance(predicates, list) or len(predicates) > 64:
            raise RetrievalError("predicates must be an array of at most 64 entries")
        pred = tuple(Predicate.from_json(p) for p in predicates)
        if any(p.axis not in axes for p in pred):
            raise RetrievalError("predicate refers to an undeclared axis")
        k = d["max_results"]
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 100:
            raise RetrievalError("max_results must be an integer 1..100")
        if type(d["exclude_reference"]) is not bool:
            raise RetrievalError("exclude_reference must be boolean")
        return cls(context, tuple(axes), reference, pred, k, d["exclude_reference"])


def load_query(path: str | Path) -> RetrievalQuery:
    return RetrievalQuery.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_corpus(records: Sequence[SpectrumRecord]) -> dict[str, SpectrumRecord]:
    """Validate a bounded in-memory corpus while retaining the P1 record profile."""
    if not isinstance(records, (tuple, list)) or not 1 <= len(records) <= 100000:
        raise RetrievalError("corpus must contain 1..100000 records")
    lookup = {}
    for record in records:
        if not isinstance(record, SpectrumRecord):
            raise RetrievalError("corpus contains a non-SpectrumRecord value")
        if (not isinstance(record.record_id, str) or not record.record_id.strip()
                or len(record.record_id) > 256 or record.record_id in lookup):
            raise RetrievalError("empty, oversized or duplicate record ID")
        for label in ("text", "context", "provenance"):
            _bounded_string(getattr(record, label), f"record.{label}", 100000)
        if not record.axes or len(record.axes) > 256:
            raise RetrievalError("record requires 1..256 numerical axes")
        if any(not isinstance(k, str) or not _IDENTIFIER.fullmatch(k) for k in record.axes):
            raise RetrievalError("record has malformed axis identifier")
        lookup[record.record_id] = record
    return lookup


def _scope(lookup: dict[str, SpectrumRecord], query: RetrievalQuery) -> tuple[SpectrumRecord, list[SpectrumRecord]]:
    reference = lookup.get(query.reference_id)
    if reference is None:
        raise RetrievalError("reference record is absent from corpus")
    if reference.context != query.context or set(reference.axes) != set(query.axes):
        raise RetrievalError("reference scope differs: explicit axis mapping/context binding required")
    if all(v.midpoint == 0 for v in reference.axes.values()):
        raise RetrievalError("reference zero vector cannot be cosine-ranked")
    rows = [r for r in lookup.values() if r.context == query.context and set(r.axes) == set(query.axes)]
    return reference, rows


class CandidateProvider(Protocol):
    """Third-party ANN adapters may implement this; results are never authoritative."""

    def candidate_ids(self, reference: SpectrumRecord) -> set[str]:
        ...


class ExactScan:
    def __init__(self, records: Sequence[SpectrumRecord]):
        self.ids = {r.record_id for r in records}

    def candidate_ids(self, reference: SpectrumRecord) -> set[str]:
        return set(self.ids)


@dataclass(frozen=True)
class LSHConfig:
    tables: int = 3
    bits: int = 8
    radius: int = 1
    seed: int = 17

    def __post_init__(self) -> None:
        if (any(isinstance(v, bool) or not isinstance(v, int) for v in (self.tables, self.bits, self.radius, self.seed))
                or not 1 <= self.tables <= 8 or not 1 <= self.bits <= 16
                or not 0 <= self.radius <= min(3, self.bits) or not 0 <= self.seed <= 65535):
            raise RetrievalError("LSH config out of bounds (tables<=8, bits<=16, radius<=3, seed<=65535)")

    def to_json(self) -> dict:
        return {"tables": self.tables, "bits": self.bits, "radius": self.radius, "seed": self.seed}


class LSHCandidateIndex:
    """Rebuildable random-hyperplane SimHash over *midpoint* features.

    Coarse retrieval may omit items; no semantic-accuracy claim is implied.
    Deterministic hashed planes avoid global random state and model dependencies.
    """

    def __init__(self, records: Sequence[SpectrumRecord], axes: Sequence[str], config: LSHConfig):
        self.axes = tuple(axes)
        if not self.axes or len(set(self.axes)) != len(self.axes):
            raise RetrievalError("LSH axes must be nonempty and unique")
        if any(set(row.axes) != set(self.axes) for row in records):
            raise RetrievalError("LSH input must be one uniform axis set; filter context/axes before indexing")
        self.config = config
        self.buckets: list[dict[int, set[str]]] = [{} for _ in range(config.tables)]
        for row in records:
            for i in range(config.tables):
                signature = self._signature(row, i)
                self.buckets[i].setdefault(signature, set()).add(row.record_id)

    def _signature(self, row: SpectrumRecord, table: int) -> int:
        coords = tuple(row.axes[a].midpoint - 0.5 for a in self.axes)
        signature = 0
        for bit in range(self.config.bits):
            total = 0.0
            for axis, value in zip(self.axes, coords):
                material = f"ISL-P3-LSH/{self.config.seed}/{table}/{bit}/{axis}".encode("ascii")
                weight = int.from_bytes(sha256(material).digest()[:8], "big") / (2**63) - 1
                total += weight * value
            if total >= 0:
                signature |= 1 << bit
        return signature

    def candidate_ids(self, reference: SpectrumRecord) -> set[str]:
        output: set[str] = set()
        for table, buckets in enumerate(self.buckets):
            anchor = self._signature(reference, table)
            for d in range(self.config.radius + 1):
                for positions in combinations(range(self.config.bits), d):
                    mask = 0
                    for bit in positions:
                        mask |= 1 << bit
                    output.update(buckets.get(anchor ^ mask, ()))
        return output


def retrieve(records: Sequence[SpectrumRecord], query: RetrievalQuery,
             method: str = "exact", lsh: LSHConfig | None = None,
             candidate_provider: CandidateProvider | None = None) -> dict:
    lookup = validate_corpus(records)
    reference, scoped = _scope(lookup, query)
    if candidate_provider is not None:
        if method != "external":
            raise RetrievalError("external provider requires method='external'")
        provider = candidate_provider
        params = None
    elif method == "exact":
        provider = ExactScan(scoped)
        params = None
    elif method == "lsh":
        cfg = lsh if lsh is not None else LSHConfig()
        provider = LSHCandidateIndex(scoped, query.axes, cfg)
        params = cfg.to_json()
    else:
        raise RetrievalError("method must be exact, lsh or external with provider")
    candidate_ids = provider.candidate_ids(reference)
    if not isinstance(candidate_ids, set) or any(not isinstance(s, str) or s not in lookup for s in candidate_ids):
        raise RetrievalError("provider returned invalid or unknown record IDs")
    eligible = []
    for rid in candidate_ids:
        row = lookup[rid]
        if row.context != query.context or set(row.axes) != set(query.axes):
            continue
        if query.exclude_reference and rid == query.reference_id:
            continue
        if not all(p.evaluate(row) for p in query.predicates):
            continue
        # Unlike a logical predicate, cosine similarity is undefined for zeros.
        if all(a.midpoint == 0 for a in row.axes.values()):
            continue
        try:
            score = midpoint_cosine(reference, row)
        except SpectrumError as exc:
            raise RetrievalError(str(exc)) from exc
        eligible.append((score, row))
    eligible.sort(key=lambda item: (-item[0], item[1].record_id))
    hits = []
    for score, row in eligible[:query.max_results]:
        text_digest = sha256(b"ISL-P3-RECORD-TEXT\0" + row.text.encode("utf-8")).hexdigest()
        hits.append({"record_id": row.record_id, "midpoint_cosine": score,
                     "text": row.text, "text_sha256": text_digest,
                     "context": row.context, "provenance": row.provenance,
                     "axes": {a: row.axes[a].to_json() for a in query.axes}})
    return {"profile": RESULT_PROFILE,
            "method": method,
            "parameters": params,
            "scope": {"context": query.context, "axes": list(query.axes)},
            "reference_id": query.reference_id,
            "predicates": [{"axis": p.axis, "endpoint": p.endpoint,
                            "operator": p.operator, "threshold": p.threshold} for p in query.predicates],
            "max_results": query.max_results,
            "excluded_reference": query.exclude_reference,
            "scope_count": len(scoped),
            "candidate_count": len(candidate_ids),
            "matched_count": len(eligible),
            "hits": hits,
            "boundary": "numerical heuristic; no logical entailment, truth, calibrated probability, or exact source recovery"}


def audit_lsh(records: Sequence[SpectrumRecord], query: RetrievalQuery, config: LSHConfig) -> dict:
    """Measure observable top-K recall against deterministic exhaustive retrieval."""
    exact = retrieve(records, query, method="exact")
    approx = retrieve(records, query, method="lsh", lsh=config)
    baseline = {hit["record_id"] for hit in exact["hits"]}
    observed = {hit["record_id"] for hit in approx["hits"]}
    return {"profile": "isl-retrieval-audit/0.3", "baseline": "exact",
            "approximate": "lsh", "parameters": config.to_json(),
            "reference_id": query.reference_id,
            "top_k": query.max_results,
            "baseline_hits": len(baseline), "approximate_hits": len(observed),
            "top_k_recall": len(baseline & observed) / len(baseline) if baseline else 1.0,
            "exact_candidate_count": exact["candidate_count"],
            "approximate_candidate_count": approx["candidate_count"],
            "scope_count": exact["scope_count"],
            "boundary": "recall against exhaustive numeric ranking, not human relevance or semantic correctness"}


def controlled_output(result: dict, style: str = "evidence") -> dict:
    """Bounded deterministic reporting, never an AI completion or source restoration."""
    if not isinstance(result, dict) or result.get("profile") != RESULT_PROFILE:
        raise RetrievalError("controlled output requires an ISL P3 retrieval result")
    if style not in ("evidence", "compact"):
        raise RetrievalError("unsupported controlled output style")
    hits = result.get("hits")
    if not isinstance(hits, list) or len(hits) > 100:
        raise RetrievalError("malformed or oversized hits")
    required = {"record_id", "midpoint_cosine", "text", "text_sha256", "context", "provenance", "axes"}
    for h in hits:
        if not isinstance(h, dict) or set(h) != required:
            raise RetrievalError("malformed hit fields")
        if not isinstance(h["record_id"], str) or not isinstance(h["text_sha256"], str):
            raise RetrievalError("malformed hit identity")
        if (not isinstance(h["text"], str)
                or sha256(b"ISL-P3-RECORD-TEXT\0" + h["text"].encode("utf-8")).hexdigest() != h["text_sha256"]):
            raise RetrievalError("hit source text digest mismatch")
    if style == "compact":
        text = "Numerical candidates: " + (", ".join(h["record_id"] for h in hits) if hits else "none")
    else:
        lines = ["ISL P3 numerical candidates (not logical conclusions):"]
        for h in hits:
            lines.append(f"[{h['record_id']}] midpoint cosine={h['midpoint_cosine']:.6f}; "
                         f"source_provenance={h['provenance']}; stored_text={json.dumps(h['text'], ensure_ascii=False)}")
        if not hits:
            lines.append("No matching records.")
        text = "\n".join(lines)
    return {"profile": OUTPUT_PROFILE,
            "style": style,
            "kind": "deterministic-template",
            "text": text,
            "references": [{"record_id": h["record_id"], "text_sha256": h["text_sha256"],
                            "provenance": h["provenance"]} for h in hits],
            "model_generated": False,
            "exact_source_recovery": False,
            "boundary": "references point to stored fields, not a byte-exact reconstruction of original source artifacts"}
