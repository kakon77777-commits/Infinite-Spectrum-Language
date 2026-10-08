# ISL P3 — Local Release Validation

**Date:** 2026-10-08  
**Version:** 0.3.0  
**Scope:** Public standalone ISL source (MIT). This file describes local evidence, not GitHub CI or independent external validation.

## Executed checks

- Python 3.13.5, `python -m unittest discover -s tests -q`: **123 tests / 0 failures**.
- `python -m compileall -q spectral_public tests`: PASS.
- P1 `.isl 0.1` check: PASS; unmodified P1 grammar and original language conformance tests retained.
- P2 adapter binding/validation demo: PASS; P2 profiles remain unchanged.
- P3 exhaustive retrieve on synthetic corpus: `near`, `middle`, `text-data` (ordered).
- P3 default LSH audit on synthetic corpus: top-3 recall `1.0`, 4 approximate candidates versus 7 exhaustive candidates; this is **not** an empirical benchmark or a guaranteed speed improvement.
- Negative-control LSH audit (`tables=1`, `bits=16`, `radius=0`, `seed=0`): top-3 recall `2/3`; approximate retrieval can omit eligible records.
- P3 controlled-output and P2 projection CLI: PASS, with source field provenance and explicit non-reconstruction/non-truth boundaries.
- `pip wheel . --no-deps --no-build-isolation`: PASS.
- Install wheel into a separate directory, then run P3 retrieval and P1 check without loading the checkout as a package: PASS.
- UTF-8 source checks and public-file boundary scan: PASS.

## Nonclaims

Local tests, invented scores and synthetic LSH recall do **not** establish semantic correctness, real-world retrieval quality, calibration, formal proof, complete ANN recall, exact source-file restoration or independent interoperability.

The GitHub CI status is reported separately by GitHub; this document does not preempt remote results.
