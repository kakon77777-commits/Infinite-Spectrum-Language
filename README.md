# ISL — Infinite Spectrum Language

**Public Research Preview P2 · v0.2.0**  
**無限光譜量化語言 · 對外研究原型**  
**Creator:** Neo.K · EveMissLab  
**Conceptual source:** *無限光譜量化語言：從語義向量到可計算語言系統* (2026-03-10)  
**License:** [MIT](LICENSE)

ISL is an independent, deliberately **bounded language prototype** for explicitly declared numerical semantic spectra. It has a tiny `.isl 0.1` interpreter and a separate optional model-neutral P2 encoding/evaluation interface.

The numbers in the language examples are **hand supplied**. P2 can accept predictions from third-party models but does **not** include a trained model. ISL is not a universal semantic reasoner, a mathematical prover, a calibrated uncertainty engine, or a completed implementation of its motivating five-layer research vision.

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

## Repository map

- [`spec/ISL_P1_LANGUAGE_SPEC.md`](spec/ISL_P1_LANGUAGE_SPEC.md) — frozen `.isl 0.1` language reference.
- [`docs/P2_MODEL_ADAPTER.md`](docs/P2_MODEL_ADAPTER.md) — optional JSON adapter contract, evaluation metrics and scientific caveats.
- [`spectral_public/`](spectral_public/) — Python reference language, interval core, adapter and evaluation code.
- [`examples/`](examples/) — `.isl` modules, JSON records and synthetic P2 fixtures.
- [`conformance/`](conformance/) — original P1 language positive and invalid corpora.
- [`tests/`](tests/) — zero-network unit tests.
- [`docs/RELEASE_SCOPE.md`](docs/RELEASE_SCOPE.md) — scope and non-goals.
- [`ROADMAP.md`](ROADMAP.md) — planned experiments.

## License

MIT License, Copyright (c) 2026 Neo.K and EveMissLab. See [LICENSE](LICENSE). The grant covers the files released in **this repository**; it does not grant rights to any separate work or technology outside this repository.

The P2 interface is a research boundary, not a certification of model accuracy, semantic truth or compatibility with any other system.
