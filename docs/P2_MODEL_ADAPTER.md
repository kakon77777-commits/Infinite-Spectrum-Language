# ISL P2 — Model-Neutral Encoding & Held-Out Evaluation

**Status:** Public Research Preview P2 / v0.2.0  
**Language syntax:** `.isl 0.1` remains unchanged.  
**License:** MIT; the P2 interface is self-contained and offline.

## 1. Intent and boundaries

P2 defines a **JSON interchange contract** for plug-in encoders that supply bounded numerical scores for explicitly declared semantic axes. No model weights, service access, tokenizer, unapproved network calls, training routine, or claim of semantic truth is part of the reference package.

- The `.isl 0.1` interpreter remains deterministic and entirely usable without P2.
- Third parties can build an encoder implementing the `SpectrumEncoder` Protocol (Python) or simply emit the versioned P2 JSON output (any language).
- An ISL score is a declared numeric descriptor under an explicit annotation/context protocol, **not** probability, truth, logically valid inference, or a universal coordinate system.
- The provided P2 examples are **synthetic invented labels and predictions**; they do not establish scientific validity, model learning or external annotation independence.

## 2. Quickstart: offline pipeline

```bash
python -m spectral_public.cli adapter-check examples/p2_requests.json examples/p2_predictions.json
python -m spectral_public.cli evaluate examples/p2_requests.json examples/p2_predictions.json examples/p2_heldout.json
python -m spectral_public.cli adapter-template examples/p2_requests.json --out my_predictions.json --encoder-name my-local-encoder --encoder-version 0.1 --run-id run-001
```

`adapter-template` writes **only explicit abstentions**, not hallucinated scores. It refuses to overwrite an existing output file. Replace each placeholder with a real model-produced interval or keep an explicit abstention. Then validate and evaluate again.

Generate demonstration fixtures deterministically:

```bash
python -m scripts.make_p2_demo
```

## 3. Versioned contracts

Request bundle (`isl-encode-requests/0.2`):

```json
{
  "profile": "isl-encode-requests/0.2",
  "items": [
    {
      "item_id": "example01",
      "text": "今天很開心。",
      "context": "朋友分享好消息",
      "context_group": "daily",
      "axes": ["joy", "calm"]
    }
  ]
}
```

Prediction bundle (`isl-encode-predictions/0.2`) has **one record per request**. The output must contain:

- `item_id` matching an existing request;
- `input_sha256` derived from the exact UTF-8 request fields (`text`, `context`, `context_group`, ordered `axes`), domain-separated and canonically serialized;
- `encoder` with nonempty `name`, `version`, `run_id`, `source` (provenance);
- `axes` mapping each declared name to `{"lower":number,"upper":number}` with finite `0 <= lower <= upper <= 1`;
- `abstain_reason`: `null` when all axes are supplied; otherwise a nonempty string with `axes: {}`.

The CLI refuses partial results, mismatched hashes, silently changing axis sets, duplicate IDs, wrong profiles, NaN, infinities, booleans as numbers, extra keys and unsupported intervals.

**Important:** SHA-256 input fingerprints are not anonymization, encryption or authentication. Do not expose private source text, contexts, people, identifiers or private model metadata in public research datasets.

## 4. Evaluation data and metrics

The held-out bundle (`isl-evaluation/0.2`) requires the literal `split: "heldout"`, an `annotation_protocol` description, and one point-label per request (`annotation_source` and complete `values`). Evaluation rejects missing/extra labels, duplicate IDs and duplicate exact input fingerprints.

The output includes:

- total requests and separately counted abstentions;
- midpoint mean absolute error (MAE) against the **declared point label**;
- point-within-proposed-interval coverage and average interval width;
- the same metrics by axis and `context_group`;
- one explicit encoder name/version/run per evaluation report.

**Coverage is NOT probability calibration.** It merely checks whether manually supplied points fall inside predicted intervals. A rigorously calibrated uncertainty model would need a precisely defined prediction target, independent annotations, calibration methodology, statistical testing and reporting of limitations.

## 5. Quality gates for a real experiment

1. Freeze the annotation protocol, axis definitions, evaluation set and split policy before inspecting model outputs.
2. Assign annotation work independently from the encoder and record provenance, inter-annotator agreement and disagreements. A field claiming independence does not establish it.
3. Avoid leakage: split by related documents, speakers and near-duplicate content; the built-in duplicate digest check catches only exact fingerprint duplicates.
4. Compare against declared non-neural / random / lexical baselines; ensure all evaluation runs use identical input/label versions.
5. Report context groups separately and include abstention rates. No aggregate score may hide failures of a specific context group.
6. Store the actual source code, the model identifier, run parameters, data hashes, and a reproducible evaluation command in an external research receipt.
7. Keep P2 interchange separate from any unpublished or proprietary engine; P2 files should be independently implementable from this document.

## 6. What remains open

P2 **does not bundle an actual trainable encoder** or an independently annotated real-world corpus. Reliable cross-model semantic alignment, robust distribution shift, calibrated uncertainty, and independent implementation conformance are subsequent research gates, not achieved properties of this synthetic fixture.
