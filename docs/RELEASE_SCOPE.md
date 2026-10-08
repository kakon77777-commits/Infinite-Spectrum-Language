# ISL Public Release Scope — P5

**Status:** Public, independently usable numerical-spectrum research prototype. **License:** MIT.

## Included and testable

- A versioned `.isl 0.1` language with five numerical operators and deterministic interpreter.
- Strict interval / axis / context / provenance / UTF-8 validation and repeatable results.
- Offline P2 external encoder interchange, exact request/context fingerprint binding, source/model version metadata and abstention.
- Point-label evaluation with context-group metrics; fully synthetic demonstration records and negative controls.
- Rebuildable candidate LSH, exhaustive baseline, exact numerical predicate rechecks and measured top-K recall against a synthetic corpus.
- Deterministic controlled-output templates clearly separated from generative model behavior and source reconstruction.
- P2-to-P3 materialization with explicitly preserved encoder provenance and abstention behavior.
- Unit/conformance tests and GitHub CI; no hard external model dependency.

## Not claimed

- Trained natural-language understanding, cross-model universal semantics or learned semantic atoms.
- Automatic discovery of an objective semantic metric, logical entailment or theorem proving.
- Independently annotated evidence, population-level generalization, calibrated confidence or reliable shift robustness.
- Native machine state, arbitrary model execution, a production security audit or compatibility with other languages.
- Real language generation, objective relevance metrics, complete recall from LSH or byte-exact restoration of original documents.

The MIT license applies only to source and documentation distributed in the ISL repository. No external or non-public technology is imported. User-submitted model adapters and datasets have their own licensing and privacy responsibilities.

## P4 public addition

An independent Node.js implementation is released under the same MIT License, but only for P1 `.isl 0.1`, P3 exhaustive numerical retrieval and bounded deterministic P3 reporting. P2 learned/model-adapter internals and P3 approximate LSH are **not** cross-runtime certified. Cross-language comparison is not external scientific validation, third-party audit or a release of any separate private project.

## P5 public addition

An offline, black-box test driver checks independently developed executables against **bounded P1/P3 synthetic contracts**. Passing this driver does **not** establish third-party authorship, a privacy/security certification, a trained natural-language model, or evidence of superior natural-language quality. No unpublished system is imported.

## Research proposal beyond P5 (not a released capability)

A separately specified future experiment may examine using **context-dependent semantic spectrum annotations** as auxiliary features for natural-language model training, pragmatic control and independent evaluation. P5 does not include a trained encoder, generator or evidence that ISL improves language naturalness. Refer to [`NATURAL_LANGUAGE_RESEARCH.md`](NATURAL_LANGUAGE_RESEARCH.md). Public examples use synthetic data; do not publish personal text, contexts or model outputs without suitable consent and rights review. See [`DATA_PRIVACY_GUIDANCE.md`](DATA_PRIVACY_GUIDANCE.md).
