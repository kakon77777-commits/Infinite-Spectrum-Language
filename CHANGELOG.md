# Changelog

## v0.4.0 — P4 independent implementation and cross-runtime conformance (2026-10-08)

- Added an independent MIT-licensed Node.js implementation of the original `.isl 0.1` language interpreter.
- Added independent P3 **exact** retrieval and bounded `compact`/`evidence` templates; P2 and approximate LSH remain Python-only.
- Added public frozen exact retrieval/output JSON vectors, JS unit tests and Python/Node differential harness (including valid, invalid and context-scoped synthetic cases).
- Updated GitHub Actions to run Python, Node.js and cross-runtime checks; documented float tolerance and verification limits.
- Preserved P1 source grammar and P2/P3 JSON contracts without new nonpublic dependencies.

## 0.3.0 (2026-10-08) — P3 Scoped Retrieval and Controlled Output

- Added context-/axis-scoped exact numerical retrieval and replaceable `CandidateProvider` interface.
- Added optional seeded random-hyperplane LSH index and exhaustive top-K recall comparison.
- Recheck source record numerical predicates after candidate retrieval; no ANN/LSH truth claims.
- Added two bounded deterministic text templates with source attribution and digest checks; no original file recovery claim.
- Added explicit offline P2 prediction-to-corpus projection with provenance and abstention handling.
- Added synthetic examples, specification, negative tests and CI smoke checks.
- Preserved P1 `.isl 0.1` grammar, P2 adapter contracts and MIT license.

## 0.2.0 (2026-10-08) — P2 Model-Neutral Encoding Boundary

- Adopted MIT license by owner decision; removed pending-license document.
- Added strictly validated encoder request/prediction JSON v0.2 with binding hashes, run provenance and explicit abstentions.
- Added offline `SpectrumEncoder` interface, deterministic fixture replay, CLI template/check/evaluate commands.
- Added synthetic held-out scoring examples, per-axis/per-context error and interval-coverage diagnostics.
- Added negative-control tests, P2 documentation, explicit limitations and updated CI.
- Preserved `.isl 0.1` grammar and existing P1 conformance/behavior.

## 0.1.0 (2026-10-08) — P1 Public Research Preview

- Added a versioned `.isl 0.1` grammar, deterministic parser/interpreter and five bounded numerical operations.
- Added mandatory context and provenance, positive/negative test fixtures and CI.
