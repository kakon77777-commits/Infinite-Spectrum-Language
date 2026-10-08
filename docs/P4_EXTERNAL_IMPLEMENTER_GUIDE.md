# External Implementer's Guide — ISL Public P4

**MIT License · Independent implementation invitation**

You can implement ISL in another language without importing the supplied Python or JavaScript code. Start with the frozen small grammar in [`spec/ISL_P1_LANGUAGE_SPEC.md`](../spec/ISL_P1_LANGUAGE_SPEC.md). The included Python and JS runtimes are references, not mandatory components of an implementation.

## What to implement first

1. Parse `isl 0.1;` files with declared axes, records, `let` and `print`.
2. Reject invalid bounds, missing metadata, duplicate identifiers, mismatched axes, and unsupported statements. Never evaluate source as host-language code.
3. Execute `intersect`, exact `union` (two intervals when disjoint), numeric `blend`, midpoint `cosine`, and source-order `filter`.
4. Produce the P1 `isl-language/0.1` JSON result with `profile`, `axes`, `records`, `outputs`.
5. Optionally support P3 **exact** retrieval; test scope equality, predicates on actual stored floats, undefined zero-cosine rejection, sort by score and ID, and SHA-256 prefixed source-text fingerprints.

## Conformance checklist

- `conformance/positive/*.isl` should succeed and match the adjacent `.expected.json` fixture, allowing only the declared binary64 comparison tolerance for numeric fields.
- `conformance/invalid/*.isl` must reject the source without executing it.
- P3 exact retrieval on `examples/p3_corpus.json` with `examples/p3_query.json` must match `conformance/p4/p3-exact.expected.json` (floating score tolerance only).
- Both P3 templates must match the respective expected JSON (including source digests).
- Check test and source revision identity; declare which language profiles your implementation supports.
- Add independent tests of malformed UTF-8, wrong profile, duplicate records, incorrect predicates, and untrusted input text.

## Contribution process

Propose changes with a failing public fixture first, then explain the normative behavior and expected compatibility impact. For numerical discrepancies, include the original numeric inputs, both observed results, and the tolerance decision. Mark new semantics as proposed until an explicit language/profile version is approved. Do not label a text similarity or an ANN hit as mathematical entailment.

Use GitHub issues/PRs to report reproducible divergence. Do **not** submit private research source, credentials, private user prompts or personal data as test fixtures. Only synthetic or redistributable sample inputs belong in this public repo.
