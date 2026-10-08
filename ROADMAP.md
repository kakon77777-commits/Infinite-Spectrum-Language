# ISL Public Research Roadmap

## P0 — bounded numerical spectrum core (implemented)

- [x] Named finite axes, intervals `[0,1]`, intersection, exact union and numeric blend.
- [x] Midpoint-cosine candidate ranking and exact axis filter.
- [x] JSON fixtures and validators.

## P1 — executable language kernel (implemented, syntax version 0.1)

- [x] Parser with source-position diagnostics, axes, records, metadata, bindings and output statements.
- [x] Deterministic reference evaluation with no network calls and negative tests.
- [x] Context/provenance, explicit mathematical interval semantics and P1 conformance fixtures.
- [x] MIT license authorized by owner and added to repository.
- [ ] Second independent language implementation and external conformance verification.

## P2 — optional model-neutral adapter and diagnostics (v0.2.0)

- [x] Explicit request / prediction interchange profiles and external encoder Protocol.
- [x] Digest binds text, context, context group and axis order; versioned encoder provenance.
- [x] Deterministic offline fixture replay and non-inventing abstention templates.
- [x] Fail-closed validation of IDs, ranges, axes, profile, digests and missing/extra records.
- [x] Held-out point-score evaluation with context-group breakdown, interval coverage and abstentions.
- [ ] Independently annotated held-out corpus, baseline comparisons and measured inter-annotator agreement.
- [ ] Real trainable encoder experiment and empirically supported calibration/shift robustness.

## P3 — retrieval and controlled output (future)

- [ ] Optional candidate indexes (ANN / LSH) with exact numerical predicate rechecks.
- [ ] Separate controlled generation quality from exact original-source recovery.

## P4 — external ecosystem validation (future)

- [ ] Independent implementation, measured conformance, community examples and extensions.
- [ ] Standardize only behaviors backed by real evidence.

Passing unit tests verifies code contracts, not objectivity of semantic dimensions, probability calibration or general language understanding.
