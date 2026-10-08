# ISL — Public Data, Privacy and Disclosure Guidance

**Status:** Public developer guidance · 2026-10-08 · P5 v0.5.0

ISL's public package ships *synthetic* records, local reference runtimes and a model-neutral interchange; it does not automatically upload source documents or telemetry. **A third-party encoder, command wrapper, data pipeline or CI job can introduce its own storage and networking.** Users must review those components separately.

## Data that can identify people

`text`, `context`, `context_group`, `provenance`, record IDs, annotations and evaluator comments may contain identifying information even without a person's name. Do not put private conversations, credentials, medical/financial details, customer data or unlicensed documents in public examples, CI artifacts, GitHub Issues, error messages or reproducibility packages. Use deliberately synthetic fixtures or authorized anonymized data wherever feasible.

`input_sha256`, text hashes and fixture digests provide **integrity or binding**, not anonymity, secrecy or authorization. Hashes of predictable content can reveal information through guessing. Do not post private source text or unique hashes derived from sensitive datasets merely because the plaintext is omitted.

## Recommended boundaries

1. Keep private training and evaluation corpora **outside the public repository** and outside public CI workspaces and logs.
2. Use purpose-specific identifiers and minimize retained source material; publish aggregate quality measures and synthetic examples when the real corpus cannot be shared.
3. Determine lawful/contractual rights before collecting, annotating, training on or redistributing external text.
4. Review every external model endpoint independently; ISL itself does not guarantee that a third-party encoder runs locally or discards its inputs.
5. Evaluate model outputs for accidental memorization, attribute disclosure and harmful inferences before public demonstration.
6. Restrict GitHub Actions permissions and inspect logs/artifacts when adding a new CI workflow.
7. Use GitHub's private commit-email option for *future* commits if you do not want a personal address shown publicly; prior Git objects retain their original author metadata unless history is deliberately rewritten.
8. `scripts/check_public_surface.py` is a **best-effort pre-publication safeguard**, not proof that the entire repository, its dependencies, Git history or generated artifacts contain no secrets. `.gitignore` likewise does not protect files already committed or manually force-added.

## What the automated guard checks

The guard examines UTF-8 source and documentation in the working tree for common literal credential formats, email addresses, private-key headers and local-user path patterns. It rejects obvious secret-file names. It reports **file path, line and category only**, never prints the suspected secret itself.

It cannot discover credentials that use unfamiliar formats, encoded values, data hidden in binary attachments, arbitrary personal facts or sensitive Git commit metadata. For a real incident, rotate affected credentials immediately; removing current files alone does not erase prior Git commits or external copies.

Run it from the project root:

```sh
python scripts/check_public_surface.py
```

Reports in this repository are examples of software conformance only, not a certification of privacy or security.
