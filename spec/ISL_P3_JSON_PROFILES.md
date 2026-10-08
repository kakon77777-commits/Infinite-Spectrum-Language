# ISL P3 JSON Profiles — Experimental v0.3

## Authority and compatibility

This is an experimental extension to the **public** ISL 0.2 research prototype. It does not alter `.isl 0.1`, P1 numerical intervals or P2 input bindings. No connection to any external or unpublished architecture is required.

- Input corpus: list of P1 `spectrum-public/0.1` records.
- Query input: `isl-retrieval-query/0.3`; precise fields in [`docs/P3_RETRIEVAL_AND_OUTPUT.md`](../docs/P3_RETRIEVAL_AND_OUTPUT.md).
- Retrieval output: `isl-retrieval-results/0.3`.
- LSH comparison: `isl-retrieval-audit/0.3`.
- Controlled output: `isl-controlled-output/0.3`.
- Explicit P2 projection receipt: `isl-p2-corpus-projection/0.3`.

## Retrieval output example (abridged, not a golden byte fixture)

```json
{
  "profile": "isl-retrieval-results/0.3",
  "method": "exact",
  "scope": {"context": "synthetic-p3-demo/context-a", "axes": ["joy", "calm"]},
  "reference_id": "anchor",
  "candidate_count": 7,
  "hits": [
    {"record_id": "near", "midpoint_cosine": 0.9999,
     "text": "這段文字是模擬相近樣本。", "text_sha256": "<hash>",
     "context": "synthetic-p3-demo/context-a",
     "provenance": "synthetic hand-authored P3 data; NOT independently measured",
     "axes": {"joy": {"lower": 0.75, "upper": 0.85}, "calm": {"lower": 0.58, "upper": 0.68}}}
  ]
}
```

The runtime also returns `parameters`, `predicates`, `max_results`, `excluded_reference`, `scope_count`, `matched_count` and an explicit claim boundary; this example is illustrative only.

## Conformance boundaries

1. Reference and candidate numerical scopes are exact text-context strings and exact axis-name sets, not ontology assertions.
2. `exact` uses every scope-eligible record; `lsh` uses the candidate set from a replaceable approximate index.
3. Every returned hit satisfies every predicate **on its original validated numerical intervals**.
4. Approximate candidate omission is explicitly possible. LSH recall must be measured against `exact` when reporting effectiveness.
5. No returned text is certified as an exact restored original file; all narrative-style output is clearly identified as a deterministic template.
6. Non-finite numbers, invalid selectors, duplicate corpus IDs, missing reference rows, invalid LSH options and unknown provider IDs fail closed.

This specification does not require a specific ANN backend, byte layout, encoder architecture or learned model. It is not a frozen inter-implementation protocol; future promotion requires independent validation.
