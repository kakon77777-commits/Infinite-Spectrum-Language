# ISL P4 — Independent Runtime and Cross-Language Conformance

**Public research release v0.4.0** · **MIT** · **2026-10-08**

## Scope and claim

P4 introduces a **second, standalone Node.js/JavaScript implementation** of the already-published P1 `.isl 0.1` language and of **P3 exact-scan retrieval + deterministic controlled output**. It is maintained in `js/` and **does not import or call the Python implementation**. Its Node.js built-ins provide UTF-8 file reading and SHA-256 hashing.

The conformance harness `scripts/p4_conformance.py` calls both runtimes from a separate driver, compares observations, and fails on divergent outputs or reject/accept decisions. It is not a third-party audit: both implementations are part of the same repository and project. Independent external reproduction remains a separate P4 open gate.

### What is independently executed

| Profile | JS support | Verified boundary |
| --- | --- | --- |
| ISL P1 grammar `isl 0.1` | yes | `run` operations and source validation |
| ISL P3 exact retrieval `isl-retrieval-query/0.3` | yes | numerical conditions, scoped midpoints, deterministic ordering |
| ISL P3 controlled output | yes | `evidence` / `compact`, source-text SHA-256 check, explicit boundary flags |
| P2 model-adapter predictions/evaluation | no | Python reference, external encoder interface remains unchanged |
| P3 approximate LSH / recall audit | no | Python reference only; approximate matches are not canonical |
| Real model training or semantics learned from data | no | outside this bounded conformance exercise |

**The success of P4 does not imply cross-language support for components shown as `no`.**

## Reproduce offline

Requires Python 3.10+ and Node.js 20+ (CI pins Node 22), no package installations for Node.

```bash
python -m unittest discover -s tests -v
node --test js/tests/p4.test.mjs
python scripts/p4_conformance.py
node js/cli.mjs run examples/hello.isl
node js/cli.mjs retrieve examples/p3_corpus.json examples/p3_query.json
node js/cli.mjs controlled-output examples/p3_corpus.json examples/p3_query.json evidence
```

The differential harness includes existing positive/invalid files plus deterministic synthetic generated programs. It also checks success/failure parity and both controlled output formats. All generated examples are artificial: no independently annotated language-understanding corpus is claimed.

## Acceptance and comparison rules

- **Exact equality**: JSON object key sets, types, booleans, strings (including Chinese text), array order, nullability, record IDs, hit ranking, source-text SHA-256 digests, scope information, and provenance.
- **Floating point**: both runtimes use IEEE-754 binary64; numbers must be finite and agree to `abs_tol=2e-12` and `rel_tol=2e-12`. These tolerances apply to comparison only; they do not redefine the P1 `isl 0.1` source language or the P3 numerical predicate, which is evaluated on the actual stored values.
- **Invalid inputs**: both runtimes must reject the test case (nonzero CLI exit). Exact diagnostic wording is not a normative requirement.
- **Evidence fields**: `model_generated=false`, `exact_source_recovery=false`, exact original text digest, and literal provenance bindings are required.
- **Security boundary**: no external commands from `.isl` input, no outgoing network, no model execution. Record text is untrusted data. An integrator must apply its own output-context escaping.
- **No false precision**: cross-language conformance does not certify objective semantics, verified mathematical inference, universal ANN performance, probability calibration, or a general-purpose language.

## Limitations and future work

1. Independent external authors must still reproduce conformance without adopting either supplied implementation.
2. Behavior outside the bounded fixtures is not globally proven equivalent; implementation bugs and new edge cases remain possible.
3. JavaScript P3 does not implement approximate LSH, and Python P3 LSH recall remains dataset-dependent.
4. Re-run the full suite for changes to the grammar, numerical operations, JSON input schema, or outputs.
5. Explicit version transitions (new syntax/profiles) are required for incompatible changes; `.isl 0.1` remains unchanged in P4.
6. Source-content digests are integrity/change fingerprints, **not** signatures, secrecy, encryption, or privacy guarantees.

The P4 goal is a **small, approachable, reproducible public ecosystem**, not a release of any separate research infrastructure.
