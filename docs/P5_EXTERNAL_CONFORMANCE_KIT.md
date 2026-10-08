# ISL P5 — External Implementation Conformance Kit

**Version:** 0.5.0 · **Date:** 2026-10-08 · **License:** MIT

## Purpose and status

This kit lets an outside implementer test a separately developed ISL runtime against **publicly frozen, bounded specifications**, without importing Python/JavaScript implementation modules. It is a self-contained **test driver**, not a third implementation and not evidence of independent third-party certification.

The project maintains Python and Node.js runtimes. Both are supplied as **self-tests of the driver**. A separate developer must still implement and submit their own runtime and evidence. A working gate never attests to *how* an implementation was written, or that it is free from copied code; reviewers must establish independence separately.

The supported conformance subset consists of:

- `isl-language/0.1`: parse and execute the frozen P1 textual grammar.
- `isl-retrieval-results/0.3`: **exact** P3 retrieval, not optional ANN/LSH results.
- `isl-controlled-output/0.3`: deterministic `compact` and `evidence` text templates.

The P2 model encoder, LSH retrieval quality, neural training, learned generation, latent semantic truth and private systems are **out of scope**. No experimental property of those systems becomes a conformance rule here.

## Runtime command-line boundary

An external implementation exposes three **trusted local** commands with filenames supplied by the test driver:

```text
isl-impl run <UTF-8 .isl file>
isl-impl retrieve <corpus.json> <query.json>
isl-impl controlled-output <corpus.json> <query.json> <compact|evidence>
```

The executable name and argument order may differ: the driver accepts explicit templates. The required properties are:

1. Exit `0` and write **one strict UTF-8 JSON object** to stdout for a valid input.
2. Exit `2` for invalid/unsupported input, write **no successful JSON to stdout**, and optionally write a diagnostic to stderr. Exit `1`, crash, timeout, or missing binary are infrastructure failures, not valid rejection.
3. Reject invalid UTF-8 source/JSON bytes, invalid scopes and non-finite fields rather than silently accepting replacement characters.
4. Preserve exact schema, strings, source IDs, array order, labels and digest fields. JSON object property ordering and insignificant output whitespace do not matter.
5. Allow bounded finite numeric comparison with absolute/relative tolerance `2e-12` on output **numeric values**; this does **not** relax the original numerical predicates.
6. Treat source strings as untrusted data, never executable commands.

A conforming implementation does not need to expose the same Python classes, JavaScript APIs, file layout, parser design, or index implementation.

## Run against a separately built runtime

Requires **Python 3.10+ only for the driver**. The runtime being tested may be written in Rust, C++, Go, JavaScript or any other language.

Example against the current Python implementation:

```bash
python scripts/p5_external_gate.py \
  --run-cmd 'python -m spectral_public.cli run {source}' \
  --retrieve-cmd 'python -m spectral_public.cli retrieve {corpus} {query}' \
  --controlled-cmd 'python -m spectral_public.cli controlled-output {corpus} {query} --style {style}'
```

Example against the independent Node implementation:

```bash
python scripts/p5_external_gate.py \
  --run-cmd 'node js/cli.mjs run {source}' \
  --retrieve-cmd 'node js/cli.mjs retrieve {corpus} {query}' \
  --controlled-cmd 'node js/cli.mjs controlled-output {corpus} {query} {style}'
```

Example against an independently implemented compiled binary:

```bash
python scripts/p5_external_gate.py \
  --workdir /path/to/other-implementation \
  --run-cmd './isl-external run {source}' \
  --retrieve-cmd './isl-external retrieve {corpus} {query}' \
  --controlled-cmd './isl-external controlled-output {corpus} {query} {style}' \
  --seed 9381 --p1-cases 24 --p3-cases 16 \
  --report /path/to/new-report.json
```

No shell is used to invoke a command. `--*-cmd` input is parsed into tokens; placeholders are replaced by absolute file paths. Execute only a binary you trust. **The test driver is not a process sandbox**; a malicious implementation could access its host machine. Run untrusted third-party executables in your own isolated CI/VM with restricted permissions and no secrets.

The default gate runs the 14 pinned public fixture files, plus bounded deterministic randomized P1/P3 cases and fail-closed negative examples. Inputs are synthetic; they are not a measure of the model's semantic comprehension. `--seed` allows repetition across independent implementations without specifying any reference interpreter as an oracle.

## Three independent acceptance layers

| Layer | Evidence required | Can be established automatically? |
| --- | --- | --- |
| Byte-frozen public vectors | SHA-256 input + golden fixture matches | Yes, driver pins bytes in `conformance/p5/MANIFEST.json` |
| Unseen synthetic probes | Independent formula-based P1/P3 oracle, seeded cases, reject behavior | Yes, for this bounded semantic surface |
| Truly independent external implementation / audit | Independent authorship, code review, environment details, external reproduction | **No**; requires external review |

The runner imports only Python standard-library modules. It does **not** import `spectral_public` or execute the project Node source unless the operator **explicitly supplies** either as the implementation under test. The expected outputs of generated cases are computed within the standalone driver from published formulas, **not by calling either runtime**.

All static golden fixture bytes are pinned; changing one requires a new recorded profile/release decision. The submitted report includes only aggregate counts, manifest digest, seed, and scope. It intentionally does not copy prompts, personal user files, process arguments, or input contents into the report.

## Acceptance claims and release wording

Allowed: **"ISL P5 has a public black-box conformance kit; Python and Node reference implementations pass it locally and in CI."**

Not allowed without separate evidence: **"Third-party independence certified", "universal semantic interchange proven", "all runtime behavior equivalent", "the encoder understands natural language", or "AI-native language complete".**

External submitters should include their repository revision, build/run instructions, full gate report, toolchain version, fixture hash, and license provenance; see `conformance/p5/SUBMISSION_TEMPLATE.json`. Do not include private papers, proprietary source, private AI conversations, secrets or sensitive personal data in public fixtures.

## Regression and versioning

Do not silently modify `isl 0.1`, P2 JSON or P3 `0.3` contracts when extending this kit. New grammar/JSON semantics require an explicit version boundary and fresh frozen vectors. Run:

```bash
python -m unittest discover -s tests -v
node --test js/tests/*.test.mjs
python scripts/p4_conformance.py
python scripts/p5_external_gate.py --run-cmd 'python -m spectral_public.cli run {source}' --retrieve-cmd 'python -m spectral_public.cli retrieve {corpus} {query}' --controlled-cmd 'python -m spectral_public.cli controlled-output {corpus} {query} --style {style}'
```

There is no remote upload, network-dependent registration, or external scoring service required by the P5 kit. Public/independent ISL remains a research line separate from other experimental implementations.
