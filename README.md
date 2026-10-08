# ISL — Infinite Spectrum Language

**Public Research Preview P1 · v0.1.0**  
**無限光譜量化語言 · 對外研究原型**  
**Creator:** Neo.K · EveMissLab  
**Conceptual source:** *無限光譜量化語言：從語義向量到可計算語言系統* (2026-03-10)

ISL is a small, independent, deliberately **bounded language prototype** for explicitly declared numerical semantic spectra. It demonstrates names for dimensions, context/provenance-carrying records, closed `[0,1]` intervals, numerical operations and deterministic queries.

The initial values are **provided by the author of each example**, not discovered from text. ISL P1 is not a language model, universal reasoning engine, neural semantic codec, theorem prover, or full implementation of the five-layer research vision.

## Quick start

No external runtime dependencies; Python 3.10+.

```bash
python -m spectral_public.cli check examples/hello.isl
python -m spectral_public.cli run examples/hello.isl
python -m spectral_public.cli run examples/disjoint.isl
python -m unittest discover -s tests -v
```

After installation with `python -m pip install .`, the same commands are available as `isl check ...` and `isl run ...`.

## The first ISL program

```isl
isl 0.1;
axis joy;
axis calm;

record morning {
  text "今天心情很好。";
  context "invented demonstration";
  provenance "hand-labeled synthetic coordinates";
  joy = [0.75, 0.90];
  calm = [0.45, 0.65];
}
record evening {
  text "今天還不錯。";
  context "invented demonstration";
  provenance "hand-labeled synthetic coordinates";
  joy = [0.60, 0.80];
  calm = [0.50, 0.70];
}

let shared = intersect(morning.joy, evening.joy);
let mixed = blend(morning.joy, evening.joy, 0.5);
let selected = filter(joy, lower >= 0.7);
print shared;
print mixed;
print selected;
```

Operations in v0.1: `intersect`, `union`, `blend`, `cosine` (midpoint **heuristic** only), and `filter` (exact numerical predicate). `union` preserves disjoint intervals; it never silently fills the gap between them.

`run` emits UTF-8 JSON describing printed values. All operations are pure local computations; there are no remote calls, AI services, filesystem writes, or executable-code evaluation inside ISL source.

## Language design / 語言設計

- **Finite execution, extensible vocabulary.** Each module declares a finite set of named axes. Later modules can use different sets. The word *Infinite* describes an open-ended research direction, not infinite physical dimensions in one computer.
- **Context & provenance are mandatory.** Numeric scores cannot be treated as objective truth without an external measurement or annotation protocol.
- **No automatic inference.** Similarity ranks numerical candidates, not logical entailments; a numerical interval does not by itself imply probability, confidence, or ambiguity.
- **A small, honest public version.** The package is self-contained; it does not require access to any private engine or unpublished source.

## Repository map

- [`spec/ISL_P1_LANGUAGE_SPEC.md`](spec/ISL_P1_LANGUAGE_SPEC.md): v0.1 grammar, semantics and error rules.
- [`spectral_public/`](spectral_public/): Python reference interpreter and P0 interval operations.
- [`examples/`](examples/): synthetic hand-annotated examples and original P0 JSON records.
- [`conformance/`](conformance/): positive JSON output fixtures and rejected invalid programs.
- [`tests/`](tests/): pure offline regression tests.
- [`docs/RELEASE_SCOPE.md`](docs/RELEASE_SCOPE.md): public capabilities and excluded internals.
- [`ROADMAP.md`](ROADMAP.md): next experimental milestones.

## Licensing and public access

This repository is **publicly readable**, but **does not yet grant an open-source license**. The owner has not finalized reuse, distribution, patent or contribution terms. See [`LICENSE_DECISION_PENDING.md`](LICENSE_DECISION_PENDING.md). Public visibility is not permission to redistribute proprietary implementations.

This project is an independent research preview. Nothing in it claims compatibility with any separate system or automatic access to non-public technology.
