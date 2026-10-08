# P5 Local Validation Report — 2026-10-08

**Status: LOCAL PASS / GitHub CI separately observable.**

This report covers the public P5 conformance *tooling*. It is not a report of an actual third-party independent implementation.

## Reproducible environment

- Python host: 3.13.5 (developer environment); CI additionally targets Python 3.10 and 3.12.
- Node.js host: v22.16.0; CI targets Node.js 22.
- Commands: `python -m unittest discover -s tests -q`, `node --test js/tests/*.test.mjs`, `python scripts/p4_conformance.py`, plus the two P5 black-box invocation examples in `docs/P5_EXTERNAL_CONFORMANCE_KIT.md`.

| Validation | Locally observed result |
| --- | --- |
| Python unit/conformance tests | 140 / 140 pass |
| Node.js independent runtime tests | 20 / 20 pass |
| P4 old-profile cross-runtime regression | PASS (147 checks) |
| P5 black-box gate against Python CLI | PASS (34 cases) |
| P5 black-box gate against Node CLI | PASS (34 cases) |
| P5 golden input hash verification | PASS (14 files pinned) |
| Invalid UTF-8 rejected (Node/Python) | PASS |
| False success output on positive test rejected by driver | PASS |
| External third-party authorship/audit | **NOT PERFORMED** |

P5 test cases are split per runtime into `p1_positive=10`, `p1_negative=6`, `p3_positive=7`, `p3_negative=9`, `controlled_positive=2`. This includes seeded synthetic cases and public positive/invalid fixtures. These are **not 34 distinct natural-language semantic proofs**, and no objective annotation accuracy is asserted.

The black-box gate uses subprocess command templates and an independent numerical formula oracle for generated cases. It does not import `spectral_public` or `js/isl_public.mjs` when calculating expectations. The attached runtime(s), however, are still owned by the same project. Passing them does not prove third-party interoperability or external independence.

## Known gaps

- No external independently authored and independently reviewed runtime has been submitted.
- The corpus is synthetic; neural model quality, general semantic interpretation and external-world validity are unmeasured.
- P2 encoders and approximate LSH are outside the P5 conformance subset.
- The gate is a test driver, **not** a secure sandbox for untrusted binaries.
- The current command rejection-exit policy is the P5 CLI conformance profile, not a retroactive change to P1 `.isl 0.1` grammar.
- Runtime compatibility evidence is bounded to the covered subsets and finite test cases, not a universal equivalence theorem.

## Release handling

GitHub release packaging includes this report, a SHA-256 manifest of every published UTF-8 source file, and the Python wheel. All project source artifacts must be independently UTF-8 decodable before public commit. Public source is MIT-licensed; no unpublished technical implementation is part of this artifact.
