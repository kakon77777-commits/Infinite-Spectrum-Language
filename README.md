# ISL — Infinite Spectrum Language

**Public Research Preview P5 · v0.5.0**  
**無限光譜量化語言 · 對外研究原型**  
**Creator:** Neo.K · EveMissLab  
**Conceptual source:** *無限光譜量化語言：從語義向量到可計算語言系統* (2026-03-10)  
**License:** [MIT](LICENSE)

ISL is an independent, deliberately **bounded language prototype** for explicitly declared numerical semantic spectra. It has a tiny `.isl 0.1` interpreter, an optional model-neutral P2 encoding/evaluation interface, and P3 numerical retrieval with optional approximate candidate discovery and deterministic output templates.

The numbers in the language examples are **hand supplied**. P2 can accept predictions from third-party models but does **not** include a trained model. P3 accepts only explicitly scoped numerical records; similarity is a heuristic, not logical inference. ISL is not a universal semantic reasoner, a mathematical prover, a calibrated uncertainty engine, or a completed implementation of its motivating five-layer research vision.

## Run the language (P1 compatibility)

No required runtime dependencies beyond Python 3.10+.

```bash
python -m spectral_public.cli check examples/hello.isl
python -m spectral_public.cli run examples/hello.isl
python -m spectral_public.cli run examples/disjoint.isl
python -m unittest discover -s tests -v
```

After `python -m pip install .`, `isl` is also installed as the CLI executable.

## Run the offline model-adapter pipeline (P2)

```bash
python -m spectral_public.cli adapter-check examples/p2_requests.json examples/p2_predictions.json
python -m spectral_public.cli evaluate examples/p2_requests.json examples/p2_predictions.json examples/p2_heldout.json
python -m spectral_public.cli adapter-template examples/p2_requests.json --out my_predictions.json --encoder-name my-local-encoder --encoder-version 0.1 --run-id run-001
```

The P2 bundle contracts include context binding, exact request hashes, encoder provenance, strict axes, range validation, explicit abstention and held-out point-score diagnostics. The example inputs, outputs and labels are **invented demonstration fixtures**, not an empirical benchmark or independently annotated evidence.

Read the [P2 specification and limitations](docs/P2_MODEL_ADAPTER.md) before attaching a real encoder. An encoder can be written in any language by producing the documented versioned JSON; `spectral_public.adapter.SpectrumEncoder` also provides an optional Python Protocol. No automatic network, telemetry, shell or model execution is introduced.

## Retrieve declared numeric spectra (P3)

```bash
# Deterministic exact numeric baseline
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json

# Optional LSH candidate narrowing; all final predicates rechecked on source rows
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json --index lsh

# Audit numerical top-K recall of LSH against exact scan
python -m spectral_public.cli retrieval-audit examples/p3_corpus.json examples/p3_query.json

# Deterministic, attributed templates (not LLM text generation)
python -m spectral_public.cli controlled-output examples/p3_corpus.json examples/p3_query.json --style evidence

# Explicit projection of external P2 predictions, without loading a model
python -m spectral_public.cli p2-corpus examples/p2_requests.json examples/p2_predictions.json --out projected.json
```

See [P3 retrieval and controlled-output contracts](docs/P3_RETRIEVAL_AND_OUTPUT.md) and [P3 experimental JSON profiles](spec/ISL_P3_JSON_PROFILES.md). P3 examples use **invented numeric annotations**; test pass rates and LSH recall do not demonstrate natural-language reasoning accuracy. The P3 reference implementation is offline and uses only Python's standard library.

## P5 — external conformance kit (portable, black-box)

P5 adds an **external-implementation verification gate**. It can test a separate executable in any language using explicit `run`, `retrieve`, and `controlled-output` command templates. It does **not** import the supplied runtime implementations when constructing expected results. Static frozen vectors and independently computed seeded synthetic cases verify public P1/P3 contracts and reject behavior.

```bash
python scripts/p5_external_gate.py \
  --run-cmd 'python -m spectral_public.cli run {source}' \
  --retrieve-cmd 'python -m spectral_public.cli retrieve {corpus} {query}' \
  --controlled-cmd 'python -m spectral_public.cli controlled-output {corpus} {query} --style {style}'

python scripts/p5_external_gate.py \
  --run-cmd 'node js/cli.mjs run {source}' \
  --retrieve-cmd 'node js/cli.mjs retrieve {corpus} {query}' \
  --controlled-cmd 'node js/cli.mjs controlled-output {corpus} {query} {style}'
```

See [external implementer's P5 guide](docs/P5_EXTERNAL_CONFORMANCE_KIT.md). **The project's own Python/Node success is NOT an independent external audit.** P2 model learning, P3 approximate LSH and semantic truth remain separate research questions.

## Your first ISL program

```isl
isl 0.1;
axis joy;
axis calm;

record morning {
  text "今天心情很好。";
  context "invented demonstration";
  provenance "hand-labeled synthetic coordinates";
  joy = [0.75, 0.90];
  calm = [0.45, 0.65];
}
record evening {
  text "今天還不錯。";
  context "invented demonstration";
  provenance "hand-labeled synthetic coordinates";
  joy = [0.60, 0.80];
  calm = [0.50, 0.70];
}

let shared = intersect(morning.joy, evening.joy);
let mixed = blend(morning.joy, evening.joy, 0.5);
let selected = filter(joy, lower >= 0.7);
print shared;
print mixed;
print selected;
```

Operations: `intersect`, `union`, `blend`, `cosine` (midpoint **heuristic**), `filter` (exact numerical predicate). Disjoint union is a two-interval set, not an invented convex hull.

## Design boundaries

- **Finite execution, extensible vocabulary.** Each actual example/module has finitely many named axes; the name *Infinite* describes the open-ended research direction, not literal infinite machine storage.
- **Context + provenance required.** Comparisons across models/axis versions require declared mappings, not a guessed universal coordinate system.
- **Numerical ≠ logical.** An interval's width cannot be silently interpreted as probability, confidence or truth. P2 `point_coverage` is a diagnostic, not verified probability calibration.
- **Independent public build.** All commands run offline. No proprietary system or unpublished code is required.
- **Retrieval is not proof.** P3 requires exact axis/context scope, checks predicates on the original numeric rows and never treats approximation as a certified conclusion.
- **Templates are not original-source recovery.** Controlled-output reports preserve source references but cannot recreate arbitrary original files.

## Repository map

- [`spec/ISL_P1_LANGUAGE_SPEC.md`](spec/ISL_P1_LANGUAGE_SPEC.md) — frozen `.isl 0.1` language reference.
- [`docs/P2_MODEL_ADAPTER.md`](docs/P2_MODEL_ADAPTER.md) — optional JSON adapter contract, evaluation metrics and scientific caveats.
- [`spec/ISL_P3_JSON_PROFILES.md`](spec/ISL_P3_JSON_PROFILES.md) — experimental retrieval/audit/output data profiles.
- [`docs/P3_RETRIEVAL_AND_OUTPUT.md`](docs/P3_RETRIEVAL_AND_OUTPUT.md) — retrieval scope, LSH limits and evidence contracts.
- [`spectral_public/`](spectral_public/) — Python reference language, intervals, adapter, evaluation, retrieval and controlled output.
- [`examples/`](examples/) — `.isl` modules, JSON records and synthetic P2 fixtures.
- [`conformance/`](conformance/) — original P1 language positive and invalid corpora.
- [`tests/`](tests/) — zero-network unit tests.
- [`docs/RELEASE_SCOPE.md`](docs/RELEASE_SCOPE.md) — scope and non-goals.
- [`ROADMAP.md`](ROADMAP.md) — planned experiments.
- [`docs/P5_EXTERNAL_CONFORMANCE_KIT.md`](docs/P5_EXTERNAL_CONFORMANCE_KIT.md) — independent executable conformance boundary and limitations.
- [`conformance/p5/MANIFEST.json`](conformance/p5/MANIFEST.json) — frozen public fixture digests and runner version.

## P4 — second independent-language implementation (Node.js)

P4 adds a standalone MIT-licensed **JavaScript / Node.js implementation** of the frozen P1 `.isl 0.1` interpreter, P3 **exhaustive** numerical retrieval and both P3 deterministic output templates. This runtime does not import or invoke Python. It does not reimplement P2 adapters or the optional approximate P3 LSH index.

```bash
node js/cli.mjs run examples/hello.isl
node js/cli.mjs retrieve examples/p3_corpus.json examples/p3_query.json
node js/cli.mjs controlled-output examples/p3_corpus.json examples/p3_query.json compact
node --test js/tests/p4.test.mjs
python scripts/p4_conformance.py
```

The differential harness compares **accept/reject behavior, full JSON shape, exact IDs, ordering, provenance and text hashes** against Python; floating-point values use a documented tolerance. This is internal **cross-language conformance**, not an external third-party audit or a claim of universal semantic correctness.

Read [P4 cross-language conformance](docs/P4_INDEPENDENT_CONFORMANCE.md), [external implementer guide](docs/P4_EXTERNAL_IMPLEMENTER_GUIDE.md), and [independent JS runtime](js/README.md). Public golden P3 exact/output fixtures live in `conformance/p4/`.

## License

MIT License, Copyright (c) 2026 Neo.K and EveMissLab. See [LICENSE](LICENSE). The grant covers the files released in **this repository**; it does not grant rights to any separate work or technology outside this repository.

The P2/P3 interfaces are research boundaries, not certifications of model accuracy, semantic truth, semantic equivalence, exact source restoration or compatibility with any other system.
