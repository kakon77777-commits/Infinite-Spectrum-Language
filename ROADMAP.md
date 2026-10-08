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
- [x] Second **host-language** implementation (P4); genuinely independent third-party validation remains open.

## P2 — optional model-neutral adapter and diagnostics (v0.2.0)

- [x] Explicit request / prediction interchange profiles and external encoder Protocol.
- [x] Digest binds text, context, context group and axis order; versioned encoder provenance.
- [x] Deterministic offline fixture replay and non-inventing abstention templates.
- [x] Fail-closed validation of IDs, ranges, axes, profile, digests and missing/extra records.
- [x] Held-out point-score evaluation with context-group breakdown, interval coverage and abstentions.
- [ ] Independently annotated held-out corpus, baseline comparisons and measured inter-annotator agreement.
- [ ] Real trainable encoder experiment and empirically supported calibration/shift robustness.

## P3 — scoped retrieval and controlled output (v0.3.0)

- [x] Scope-checked exhaustive numerical retrieval, recorded context and provenance.
- [x] Optional rebuildable random-hyperplane LSH for candidate discovery; exact stored-number predicate recheck.
- [x] Explicit approximate top-K recall audit against exhaustive ranking (synthetic fixtures only).
- [x] Bounded deterministic templates that never claim model generation or original-file restoration.
- [x] P2 predictions projected to source records with exact input binding and model provenance.
- [ ] Empirical LSH trade-off benchmarks on externally annotated data.
- [ ] Learned constrained generation with separate factuality/recovery evaluation.

## P4 — independent Node.js implementation and cross-language checks (v0.4.0)

- [x] Second host-language implementation of P1 `.isl 0.1`, independent of Python runtime.
- [x] Independent P3 exact-scan retrieval and deterministic controlled output.
- [x] Frozen public P3 golden fixtures; language and retrieval differential tests with deterministic synthetic cases.
- [x] GitHub CI for Python 3.10/3.12, Node.js, and mandatory cross-language conformance.
- [x] External implementer instructions, known limitations and rejection-path coverage.
- [ ] Independent **third-party** implementation/audit outside the project.
- [ ] External annotated datasets, reproducible semantic/latency benchmarks and diverse community-contributed fixtures.
- [ ] Only standardize further behavior after independent evidence; preserve versioned boundary on incompatible changes.

## P5 — external conformance tooling (v0.5.0)

- [x] Published a reference-independent **black-box** gate that launches user-supplied CLI commands without importing internal runtime code.
- [x] Frozen SHA-256 digests of existing public golden vectors and bounded profile-specific JSON comparison.
- [x] Deterministic generated P1/P3 test cases with a standalone formula-based numerical oracle (not a reference runtime oracle).
- [x] Strict rejection of malformed JSON/UTF-8 with reproducible negative cases.
- [x] Runtime-neutral submission template, external implementer guide and public divergence issue template.
- [ ] **Real third-party** authorship and independently reviewed execution receipts.
- [ ] Validation on externally annotated data with measured cross-implementation behavior beyond bounded synthetic fixtures.

## Proposed research track — spectrum-aware natural-language learning and evaluation (not implemented)

- [ ] Define annotation protocols for context-dependent style, pragmatic intent, and semantic fidelity; avoid claiming universal axes.
- [ ] Establish lawful, independently annotated, privacy-reviewed corpora and held-out splits by speaker/source/domain; measure annotator disagreement.
- [ ] Train or attach an optional **external** encoder via the P2 interchange without changing the stable `.isl 0.1` language.
- [ ] Compare matched-budget baselines (no ISL / auxiliary spectrum supervision / optional spectrum-conditioned control), including ablations and negative controls.
- [ ] Conduct blinded human naturalness and contextual-appropriateness evaluation; separately measure meaning preservation, factuality, latency and cost.
- [ ] Publish reproducible results and failures before describing the approach as an improvement.

This is a **proposed evaluation program**, not a P6 release commitment or a claim that language-model training is included in P5. See [`docs/NATURAL_LANGUAGE_RESEARCH.md`](docs/NATURAL_LANGUAGE_RESEARCH.md).

Passing unit tests verifies code contracts, not objectivity of semantic dimensions, probability calibration or general language understanding.
