# ISL Public Research Roadmap

## P0 — bounded numerical spectrum core (implemented)

- [x] Explicit names and intervals bounded to `[0,1]`.
- [x] Intersection, true disjoint union, numeric blend.
- [x] Midpoint-cosine candidate similarity and exact range filter.
- [x] JSON validation and synthetic fixtures.

## P1 — executable language kernel (current)

- [x] Small versioned grammar with a parser and source-position diagnostics.
- [x] Axis, record, metadata, operation binding, and output statements.
- [x] Strict runtime checks and deterministic reference evaluation.
- [x] Positive and rejected-invalid conformance corpora; offline regression tests.
- [x] Separate mathematical interval semantics from uncertainty or probability.
- [ ] Second independent implementation / external conformance validation.
- [ ] Owner-selected distribution and code license.

## P2 — optional model adapter (future)

- [ ] Model-neutral encoding interface with provenance / model version.
- [ ] Evaluate against held-out, independently annotated examples.
- [ ] Track context shift, uncertainty calibration, and failure modes.

## P3 — retrieval and controlled output (future)

- [ ] ANN/LSH only as replaceable candidate-discovery accelerators.
- [ ] Always recheck numerical predicates exactly.
- [ ] Controlled generation evaluated separately from source restoration.

## P4 — independent ecosystem validation (future)

- [ ] Independent language implementation and measured conformance.
- [ ] Community-maintained examples and error-case extension.
- [ ] Standardize only behaviors backed by actual evidence.

P0/P1 implementations are limited research tools. Their passing unit tests are not evidence that semantic representations are objective or that arbitrary linguistic reasoning has been solved.
