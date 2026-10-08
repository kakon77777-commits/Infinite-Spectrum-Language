# ISL Public — independent Node.js runtime (P4)

This directory is a separate, MIT-licensed JavaScript implementation. It does **not** import the `spectral_public` Python package, contact a server, or use any private ISQL implementation.

Requirements: Node.js 20+ (CI tests 22); standard library only. The package is deliberately not published to npm yet.

```bash
node js/cli.mjs run examples/hello.isl
node js/cli.mjs retrieve examples/p3_corpus.json examples/p3_query.json
node js/cli.mjs controlled-output examples/p3_corpus.json examples/p3_query.json compact
node --test js/tests/p4.test.mjs
python scripts/p4_conformance.py
```

**Implemented:** P1 grammar and evaluation, P3 **exact** scan retrieval and two bounded controlled templates. **Not implemented:** P2 model adapter, P3 approximate LSH, arbitrary source-document recovery, learned encoding or general inference.

The Python cross-language driver is only a **test harness**; the Node runtime and its own unit tests run without Python. Read [`docs/P4_INDEPENDENT_CONFORMANCE.md`](../docs/P4_INDEPENDENT_CONFORMANCE.md) for exact conformance limits and [`docs/P4_EXTERNAL_IMPLEMENTER_GUIDE.md`](../docs/P4_EXTERNAL_IMPLEMENTER_GUIDE.md) for building a third implementation.
