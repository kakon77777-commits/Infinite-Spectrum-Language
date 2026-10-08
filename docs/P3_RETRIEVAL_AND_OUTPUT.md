# ISL P3 — Scoped Retrieval and Controlled Output (v0.3)

**Status:** bounded public experimental profile; no private systems, no automatic model execution.  
**License:** MIT.  
**Language compatibility:** `.isl 0.1` remains unchanged. This document defines separate offline JSON/CLI profiles.

## 1. What P3 implements

1. **Exact scan (baseline)** over validated P1 `spectrum-public/0.1` records.
2. **Replaceable candidate selection** via `CandidateProvider`. A deterministic, dependency-free random-hyperplane LSH candidate index is included. Third-party ANN implementations can supply IDs through the Python protocol but have no normative ranking authority.
3. **Exact rechecking** of every selected record's declared numerical predicates; only validated source record values are authoritative. The term *exact* here means checking the stored float fields, **not** arbitrary-precision mathematics or an exact semantic meaning.
4. **Scoped midpoint-cosine numerical ranking** over explicitly matching context string and axis name set. These numbers are not logical entailment, objective similarity or calibrated probabilities.
5. **Audited approximation**: compare a particular LSH run with the exhaustive top-K numeric ranking and report empirical recall for that corpus/query.
6. **Controlled output**: two bounded deterministic text templates with record IDs, provenance and stored-text fingerprints. Neither is an AI text generator nor an exact original-source reconstruction.
7. **P2 projection**: externally supplied, validated P2 predictions can be emitted as P1 records with encoder provenance and explicit non-truth labels, without rerunning the model.

## 2. Quick start

```bash
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json --index lsh --tables 3 --bits 8 --radius 1 --seed 17
python -m spectral_public.cli retrieval-audit examples/p3_corpus.json examples/p3_query.json
python -m spectral_public.cli controlled-output examples/p3_corpus.json examples/p3_query.json --style evidence
python -m spectral_public.cli controlled-output examples/p3_corpus.json examples/p3_query.json --style compact
python -m spectral_public.cli p2-corpus examples/p2_requests.json examples/p2_predictions.json --out projected.json
```

The `p2-corpus` command uses exclusive file creation and **refuses to overwrite** an existing output path.

All demonstration data is invented and manually constructed; no independent annotation, training or language understanding has been measured.

## 3. Query contract

A file with `profile = "isl-retrieval-query/0.3"` must contain **exactly**:

```json
{
  "profile": "isl-retrieval-query/0.3",
  "context": "synthetic-p3-demo/context-a",
  "axes": ["joy", "calm"],
  "reference_id": "anchor",
  "predicates": [
    {"axis": "joy", "endpoint": "lower", "operator": ">=", "threshold": 0.6}
  ],
  "max_results": 3,
  "exclude_reference": true
}
```

- `context` is an **exact string scope**, not automatically inferred context equivalence.
- `axes` contains 1–256 unique ASCII identifiers. The reference and every candidate compared must share exactly those axis names; no implicit version, scale or domain conversion.
- `reference_id` identifies the existing, nonzero-midpoint reference row within the declared context/axes.
- `predicates` has at most 64 entries, each inspecting a stored `lower` or `upper` endpoint with `>=` or `<=` and a finite threshold in `[0,1]`. Empty predicates are allowed.
- `max_results` is 1–100. `exclude_reference` is a boolean.
- Corpus records use the already published `spectrum-public/0.1` profile and require text, context, provenance and non-empty numeric axes.
- Cross-context or cross-encoder comparison **is not supported by a mapping contract in P3**; a developer must not treat coincidentally identical axis names as proven shared semantics. P2 records retain their original per-request context and are therefore not automatically comparable across differing contexts.

## 4. Candidate-index contract

A candidate provider supplies `candidate_ids(reference)` returning a set of existing record IDs. The runtime:

1. rejects missing/invalid reference, unknown IDs or a malformed provider result;
2. narrows to identical context and axis sets;
3. applies actual stored-number predicates, never candidate-stage approximations;
4. rejects cosine-undefined all-zero candidate vectors;
5. computes midpoint cosine from the actual stored numerical intervals;
6. sorts descending by score, breaking ties lexicographically by record ID;
7. returns at most `max_results` with source text, record ID, context, provenance and a deterministic text digest.

P3's built-in LSH is a **rebuildable, approximate candidate generator** based on 0.5-centered numeric midpoints, seeded hashed random hyperplanes, multiple tables and Hamming-radius probing. It is not a learned embedding, a universal semantic index, a normative wire format or evidence of general ANN performance.

Parameters: tables 1–8, bits 1–16, radius 0–3 (not exceeding bits), seed 0–65535. The default is 3 tables, 8 bits, radius 1, seed 17. Changing these values may alter recall and latency. Similarity **ranking** is always recomputed from the original rows, but incomplete candidate recall can omit otherwise eligible hits.

`retrieval-audit` compares the LSH top-K IDs against exhaustive top-K IDs for the **same numerical dataset/query**, returning `top_k_recall`. It does **not** measure human relevance or correctness of the underlying semantic dimensions.

## 5. Controlled output contract

P3 `isl-controlled-output/0.3` supports:

- `evidence`: a deterministic report of each selected source record's ID, numeric score, declared provenance and escaped stored text;
- `compact`: a deterministic single-line list of selected record IDs.

Both include `model_generated = false`, `exact_source_recovery = false`, `kind = "deterministic-template"`, and source text hashes. A hash is a content-change fingerprint for the stored field, **not** a privacy mechanism, a signature or original-document byte restoration. The renderer checks the text digest again and refuses tampered values.

User-provided source text is **untrusted data**. These templates never execute instructions contained within that text. If integrating output into HTML or a model prompt, applications must escape rendering surfaces and treat those fields as untrusted input.

## 6. P2 → P3 boundary

`p2-corpus` revalidates P2 input digest, IDs, axis schema and abstentions; it rejects predictions whose encoder name/version/run/source differ. It emits only non-abstaining scores, with explicit `external P2 score prediction` provenance, original input text, original input context, the declared group name and original input digest. It does **not** claim those scores are experimentally valid or comparable across unknown contexts.

This is a useful *data-interface bridge*, not a trained encoder, a mathematical prover, a probability-calibrated model or a source-document recovery process.

## 7. Known limitations and next gates

- LSH is an optional numerical candidate filter. Production ranking, indexing across multiple records' coordinate systems, measured ANN performance and distributed index deployment are not part of P3.
- No learned encoder is included. The demo labels and score intervals are invented.
- Python double precision is the reference numerical basis for this bounded profile; behavior is not a formal real-number arithmetic specification.
- Raw text/context/provenance are present in query results; users must not pass private content to an untrusted consumer or public service.
- A real language generator with constraint satisfaction, factuality tests or measurable restoration fidelity remains future research.
- Independent implementation, external conformance, empirical benchmark corpora and protocol freeze remain separate future gates.

**Research principle:** accepted candidate IDs are evidence of index discovery only. Final numeric predicates are checked on source data. A numeric match does not imply semantic or logical truth.
