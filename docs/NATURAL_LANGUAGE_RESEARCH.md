# ISL — Semantic Spectrum Companions for Natural-Language Research

**Status:** Public, non-normative research proposal · 2026-10-08  
**Repository:** ISL P5 v0.5.0 · MIT  
**Research question:** Can explicit, context-conditioned semantic-spectrum descriptors improve *human-perceived naturalness and pragmatic appropriateness* when used **alongside** an existing language model?

## 1. Position and motivation

ISL began with the idea of representing some continuous, contextual semantic variation as computable spectra. This suggests a **testable adjunct** to existing text models: use declared spectrum descriptors to analyze, train, condition, or assess forms of expression. It is **not** proposed as the only training data, a universal semantic ontology, a replacement for token-based language models, or proof that natural language is entirely continuous.

A language model may generate fluent text without ISL. ISL's hypothesized contribution is to make selected variation (for example, directness, formality, warmth, affective intensity or degree of explicitness) **measurable under a declared annotation protocol** and potentially easier to audit or control.

**Crucial distinction:** fluency, naturalness, social appropriateness, truthfulness and preservation of speaker intent are different properties. Optimizing one can harm another. No numerical axis alone certifies a sentence as natural or correct.

## 2. Candidate application modes

| Mode | What ISL could contribute | Existing P5 support | Still needed |
| --- | --- | --- | --- |
| Annotation/analysis | Record context-scoped human or model-proposed spectra | P1 numeric storage, P2 external adapter | Reliable annotations and axes |
| Auxiliary training | Supply spectrum-label or consistency objectives alongside normal text training | P2 interchange **only** | Trainable external model and ablation |
| Controlled expression | Request a context-specific expression range, then check meaning retention | Numeric range operations only | Real generator, constraints and evaluators |
| Independent evaluation | Slice results by axis and context and check annotation errors | Synthetic P2 evaluation, P3 query | Human naturalness trials, real held-out corpus |

These are *distinct experiments*, not one implemented end-to-end system.

## 3. Context, ambiguity and semantics

A sentence's pragmatic effect depends on roles, social relationship, communicative purpose, culture, genre and interaction history. A single global `politeness = 0.8` value has no reliable interpretation without a protocol, domain and population. Define each axis with anchors, inclusion/exclusion criteria, annotation disagreement and a versioned scale.

Example research design (not measured): compare a firm scheduling request with a gentle invitation under different workplace/friend contexts. Preserve the original intent, obligation and factual content. A superficially friendlier phrasing that changes a compulsory appointment into an optional invitation **fails the meaning-preservation gate**, even if preferred by raters.

Intervals in ISL express **declared numerical ranges**. Do not equate interval width with probability, epistemic confidence or pragmatic ambiguity without separately validated semantics. Encoder outputs are candidate annotations, not authoritative facts.

## 4. Reproducible experimental design

1. **Data governance before training.** Use appropriately licensed or consented source text, document its provenance and any permitted AI use, and remove unnecessary identifiers. Do not train/evaluate on personal conversations without authorization.
2. **Freeze a protocol.** Specify tasks, axis definitions, context features, annotation rubrics, abstention rules and acceptance thresholds before examining outcomes.
3. **Use independent human annotation.** Employ multiple raters; report disagreement, inter-annotator agreement, cultural/domain variation and unresolved ambiguities. Avoid asking the same model to make and certify its own labels.
4. **Prevent leakage.** Separate training, validation and final evaluation by speakers, originating documents, domains and near duplicates. Do not let paraphrases of the held-out set leak into training or prompt selection.
5. **Compare controlled baselines.** Use equivalent underlying model, data budget and compute: **A** = ordinary baseline, **B** = baseline with spectrum auxiliary supervision, **C** = B plus optional spectrum-conditioned control. An ablation without valid context information is a useful negative control.
6. **Blind evaluation.** Independent evaluators rate perceived naturalness, context appropriateness, intended meaning retention, factual fidelity and readability. Evaluate separately from ISL's own numeric consistency diagnostics.
7. **Cost and failure accounting.** Report abstention, bias or subgroup variation, instability, latency, training/inference cost, and examples where ISL is neutral or harmful. Include confidence intervals or uncertainty estimates appropriate to sample size.
8. **Reproducible report.** Publish dataset/annotation version hashes, train/eval split policy, model settings, random seeds, scorer definitions and eligible sample counts without releasing restricted records.

**Success would mean a demonstrated gain on independent outcome measures**, not merely that a model predicts its own chosen spectrum axes more accurately.

## 5. Relationship to current ISL

- **P1 / `.isl 0.1`:** deterministic interval operations over explicitly supplied spectra.
- **P2:** optional *model-neutral* prediction JSON, context binding, provenance and synthetic held-out diagnostics.
- **P3:** exact numerical retrieval plus optional approximate candidate discovery; templated outputs are not real natural-language generation.
- **P4–P5:** independently implemented language runtime and externally executable numerical conformance gates; no evaluation of linguistic naturalness.

No new grammar, protocol version, pretrained weights or network dependency is introduced by this document. External teams can explore the proposed use independently. It does not imply that unpublished components are needed or licensed.

## 6. Release claims

**Permitted today:** "ISL is an MIT-licensed research language with explicit numerical semantic-spectrum representations, model-neutral adapter interfaces and offline evaluation scaffolding. We propose studying it as an auxiliary layer for natural-language training and evaluation."

**Not supported today:** "ISL already makes language models more natural," "ISL learns semantics without annotation," "ISL scores certify human intent," or "ISL P5 ships a spectrum-trained language model."

See [`DATA_PRIVACY_GUIDANCE.md`](DATA_PRIVACY_GUIDANCE.md) before attaching real corpora or publishing reports.
