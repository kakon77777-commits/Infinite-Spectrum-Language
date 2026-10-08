# Changelog

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
