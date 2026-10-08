"""P3 positive, negative, approximate-recall and isolation regression tests."""
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path

from spectral_public.adapter import load_requests, load_predictions
from spectral_public.cli import load, main
from spectral_public.core import SpectrumRecord
from spectral_public.p2_projection import project_predictions
from spectral_public.retrieval import (
    QUERY_PROFILE, OUTPUT_PROFILE, RESULT_PROFILE, LSHCandidateIndex,
    ExactScan, LSHConfig, Predicate, RetrievalError, RetrievalQuery,
    audit_lsh, controlled_output, load_query, retrieve, validate_corpus,
)

ROOT = Path(__file__).resolve().parents[1]


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load(str(ROOT / "examples/p3_corpus.json"))
        cls.query = load_query(ROOT / "examples/p3_query.json")

    def q(self, **changes):
        raw = json.loads((ROOT / "examples/p3_query.json").read_text(encoding="utf-8"))
        raw.update(changes)
        return RetrievalQuery.from_json(raw)

    def test_exact_results_sorted_deterministic(self):
        first = retrieve(self.records, self.query)
        second = retrieve(list(reversed(self.records)), self.query)
        self.assertEqual(first, second)
        self.assertEqual(first["profile"], RESULT_PROFILE)
        self.assertEqual([hit["record_id"] for hit in first["hits"]], ["near", "middle", "text-data"])
        self.assertEqual(first["scope_count"], 7)

    def test_conformance_expected_ids(self):
        fixture = json.loads((ROOT / "conformance/p3.expected-ids.json").read_text(encoding="utf-8"))
        hits = retrieve(self.records, self.query)["hits"]
        self.assertEqual([h["record_id"] for h in hits], fixture["expected_hit_ids"])

    def test_filter_is_exact_on_source_value(self):
        out = retrieve(self.records, self.query)
        for hit in out["hits"]:
            self.assertGreaterEqual(hit["axes"]["joy"]["lower"], 0.6)
        self.assertNotIn("off", [h["record_id"] for h in out["hits"]])

    def test_other_context_and_axis_set_excluded(self):
        out = retrieve(self.records, self.q(predicates=[]))
        ids = {h["record_id"] for h in out["hits"]}
        self.assertNotIn("outside", ids)
        self.assertNotIn("otheraxes", ids)

    def test_reference_can_be_included(self):
        out = retrieve(self.records, self.q(exclude_reference=False))
        self.assertEqual(out["hits"][0]["record_id"], "anchor")

    def test_reference_excluded(self):
        self.assertNotIn("anchor", {h["record_id"] for h in retrieve(self.records, self.query)["hits"]})

    def test_zero_candidates_not_ranked(self):
        out = retrieve(self.records, self.q(predicates=[]))
        self.assertNotIn("zero", {h["record_id"] for h in out["hits"]})

    def test_missing_reference_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "absent"):
            retrieve(self.records, self.q(reference_id="missing"))

    def test_scope_mismatch_reference_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "scope"):
            retrieve(self.records, self.q(reference_id="outside"))

    def test_zero_reference_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "zero vector"):
            retrieve(self.records, self.q(reference_id="zero"))

    def test_query_context_restriction(self):
        with self.assertRaisesRegex(RetrievalError, "scope"):
            retrieve(self.records, self.q(context="not the context"))

    def test_empty_results(self):
        result = retrieve(self.records, self.q(predicates=[{"axis": "joy", "endpoint": "lower", "operator": ">=", "threshold": 1}]))
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["matched_count"], 0)

    def test_exact_provider_returns_all_scoped(self):
        result = ExactScan(self.records).candidate_ids(self.records[0])
        self.assertEqual(len(result), len(self.records))

    def test_lsh_deterministic_with_stable_candidates(self):
        config = LSHConfig(3, 8, 1, 17)
        ref = self.records[0]
        scoped = [r for r in self.records if set(r.axes) == set(self.query.axes)]
        idx1 = LSHCandidateIndex(scoped, self.query.axes, config)
        idx2 = LSHCandidateIndex(list(reversed(scoped)), self.query.axes, config)
        self.assertEqual(idx1.candidate_ids(ref), idx2.candidate_ids(ref))
        self.assertIn("anchor", idx1.candidate_ids(ref))

    def test_lsh_incompatible_axes_rejected(self):
        with self.assertRaises(RetrievalError):
            LSHCandidateIndex(self.records, self.query.axes, LSHConfig())

    def test_lsh_post_filter_never_emits_invalid_predicates(self):
        result = retrieve(self.records, self.query, "lsh", LSHConfig())
        for hit in result["hits"]:
            self.assertEqual(hit["context"], self.query.context)
            self.assertGreaterEqual(hit["axes"]["joy"]["lower"], .6)

    def test_lsh_audit_range(self):
        summary = audit_lsh(self.records, self.query, LSHConfig())
        self.assertEqual(summary["profile"], "isl-retrieval-audit/0.3")
        self.assertGreaterEqual(summary["top_k_recall"], 0)
        self.assertLessEqual(summary["top_k_recall"], 1)
        self.assertLessEqual(summary["approximate_candidate_count"], summary["scope_count"])

    def test_lsh_can_miss_true_top_k(self):
        # Negative control: a restrictive one-table LSH is not guaranteed to find all hits.
        audit = audit_lsh(self.records, self.query, LSHConfig(tables=1, bits=16, radius=0, seed=0))
        self.assertLess(audit["top_k_recall"], 1)

    def test_lsh_no_context_contamination(self):
        approx = retrieve(self.records, self.query, "lsh", LSHConfig())
        self.assertNotIn("outside", [h["record_id"] for h in approx["hits"]])

    def test_lsh_bounded_invalid_params(self):
        for bad in [dict(tables=0), dict(bits=17), dict(radius=4), dict(seed=-1), dict(bits=True), dict(radius=-1)]:
            with self.subTest(bad=bad), self.assertRaises(RetrievalError):
                LSHConfig(**bad)

    def test_external_candidate_false_positive_recheck(self):
        class Fake:
            def candidate_ids(self, reference):
                return {"anchor", "off", "near", "outside"}
        out = retrieve(self.records, self.query, "external", candidate_provider=Fake())
        self.assertEqual([h["record_id"] for h in out["hits"]], ["near"])

    def test_external_unknown_id_rejected(self):
        class Fake:
            def candidate_ids(self, reference):
                return {"unknown"}
        with self.assertRaisesRegex(RetrievalError, "provider"):
            retrieve(self.records, self.query, "external", candidate_provider=Fake())

    def test_external_wrong_return_type_rejected(self):
        class Fake:
            def candidate_ids(self, reference):
                return ["near"]
        with self.assertRaises(RetrievalError):
            retrieve(self.records, self.query, "external", candidate_provider=Fake())

    def test_external_wrong_method_rejected(self):
        class Fake:
            def candidate_ids(self, reference):
                return {"near"}
        with self.assertRaises(RetrievalError):
            retrieve(self.records, self.query, "exact", candidate_provider=Fake())

    def test_unsupported_method(self):
        with self.assertRaises(RetrievalError):
            retrieve(self.records, self.query, "nope")

    def test_compact_output_not_ai_or_source_restore(self):
        out = controlled_output(retrieve(self.records, self.query), "compact")
        self.assertEqual(out["profile"], OUTPUT_PROFILE)
        self.assertFalse(out["model_generated"])
        self.assertFalse(out["exact_source_recovery"])
        self.assertEqual(len(out["references"]), 3)

    def test_evidence_output_is_attributed(self):
        out = controlled_output(retrieve(self.records, self.query), "evidence")
        self.assertIn("synthetic hand-authored", out["text"])
        self.assertIn("[near]", out["text"])
        self.assertNotIn("original file recovered", out["text"])

    def test_adversarial_source_is_data_only(self):
        out = controlled_output(retrieve(self.records, self.q(max_results=10)), "evidence")
        self.assertIn("Ignore prior instructions", out["text"])
        self.assertFalse(out["model_generated"])

    def test_empty_render(self):
        result = retrieve(self.records, self.q(predicates=[{"axis": "calm", "endpoint": "upper", "operator": "<=", "threshold": .0}]))
        out = controlled_output(result, "compact")
        self.assertEqual(out["text"], "Numerical candidates: none")

    def test_bad_render_style(self):
        with self.assertRaises(RetrievalError):
            controlled_output(retrieve(self.records, self.query), "prose-ai")

    def test_bad_render_profile(self):
        with self.assertRaises(RetrievalError):
            controlled_output({"profile": "other"})

    def test_controlled_output_rejects_tampered_text(self):
        result = retrieve(self.records, self.query)
        result["hits"][0]["text"] = "tampered"
        with self.assertRaisesRegex(RetrievalError, "digest mismatch"):
            controlled_output(result)

    def test_record_source_text_hash_is_stable(self):
        first = retrieve(self.records, self.query)
        second = retrieve(self.records, self.query)
        self.assertEqual(first["hits"][0]["text_sha256"], second["hits"][0]["text_sha256"])

    def test_invalid_query_schema(self):
        for field, value in [("profile", "wrong"), ("context", ""), ("axes", ["joy", "joy"]),
                             ("axes", []), ("max_results", True), ("max_results", 0),
                             ("max_results", 101), ("exclude_reference", "yes"),
                             ("predicates", "wrong")]:
            with self.subTest(field=field, value=value), self.assertRaises(RetrievalError):
                self.q(**{field: value})

    def test_invalid_predicates(self):
        for bad in [dict(axis="xyz", endpoint="lower", operator=">=", threshold=0.1),
                    dict(axis="joy", endpoint="lower", operator=">", threshold=0.1),
                    dict(axis="joy", endpoint="midpoint", operator=">=", threshold=0.1),
                    dict(axis="joy", endpoint="lower", operator=">=", threshold=True),
                    dict(axis="joy", endpoint="lower", operator=">=", threshold=float('nan'))]:
            with self.subTest(bad=bad), self.assertRaises(RetrievalError):
                self.q(predicates=[bad])

    def test_predicate_untouched_source_numeric(self):
        ref = self.records[1]
        predicate = Predicate.from_json({"axis":"joy", "endpoint":"lower", "operator":">=", "threshold":.75})
        self.assertTrue(predicate.evaluate(ref))

    def test_duplicate_record_rejected(self):
        with self.assertRaisesRegex(RetrievalError, "duplicate"):
            validate_corpus(self.records + [self.records[0]])

    def test_non_record_rejected(self):
        with self.assertRaises(RetrievalError):
            validate_corpus([{"fake": True}])

    def test_retrieval_empty_corpus_rejected(self):
        with self.assertRaises(RetrievalError):
            retrieve([], self.query)

    def test_cli_retrieve_roundtrip(self):
        with redirect_stdout(StringIO()) as stdout:
            code = main(["retrieve", str(ROOT / "examples/p3_corpus.json"), str(ROOT / "examples/p3_query.json")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["profile"], RESULT_PROFILE)

    def test_cli_retrieval_audit(self):
        with redirect_stdout(StringIO()) as stdout:
            code = main(["retrieval-audit", str(ROOT / "examples/p3_corpus.json"), str(ROOT / "examples/p3_query.json")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["profile"], "isl-retrieval-audit/0.3")

    def test_cli_controlled_output(self):
        with redirect_stdout(StringIO()) as stdout:
            code = main(["controlled-output", str(ROOT / "examples/p3_corpus.json"), str(ROOT / "examples/p3_query.json"), "--style", "compact"])
        self.assertEqual(code, 0)
        self.assertIn("Numerical candidates", json.loads(stdout.getvalue())["text"])

    def test_cli_invalid_query_exits_2(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "bad.json"
            file.write_text('{"bad":"query"}', encoding="utf-8")
            with redirect_stderr(StringIO()) as stderr:
                code = main(["retrieve", str(ROOT / "examples/p3_corpus.json"), str(file)])
            self.assertEqual(code, 2)
            self.assertIn("ISL error", stderr.getvalue())

    def test_cli_lsh_end_to_end(self):
        with redirect_stdout(StringIO()) as stdout:
            code = main(["retrieve", str(ROOT / "examples/p3_corpus.json"), str(ROOT / "examples/p3_query.json"), "--index", "lsh", "--radius", "1"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["method"], "lsh")


class P2ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = load_requests(ROOT / "examples/p2_requests.json")
        cls.predictions = load_predictions(ROOT / "examples/p2_predictions.json")

    def test_projection_preserves_all_nonabstained(self):
        records, receipt = project_predictions(self.requests, self.predictions)
        self.assertEqual(receipt["materialized"], 8)
        self.assertEqual(len(records), 8)
        self.assertTrue(all(row["profile"] == "spectrum-public/0.1" for row in records))
        self.assertIn("not verified semantic truth", records[0]["provenance"])
        self.assertEqual(records[0]["context"], self.requests[0].context)
        for r in records:
            SpectrumRecord.from_json(r)

    def test_projection_filters_abstentions(self):
        from spectral_public.adapter import EncodePrediction
        preds = list(self.predictions)
        first = preds[0]
        preds[0] = EncodePrediction(first.item_id, first.input_sha256, first.encoder, {}, "unknown")
        records, receipt = project_predictions(self.requests, preds)
        self.assertEqual(len(records), 7)
        self.assertEqual(receipt["abstained"], 1)

    def test_projection_rejects_cross_encoder_cohort(self):
        from spectral_public.adapter import EncoderInfo, EncodePrediction
        preds = list(self.predictions)
        first = preds[0]
        altered = EncoderInfo(first.encoder.name, first.encoder.version, "another-run", first.encoder.source)
        preds[0] = EncodePrediction(first.item_id, first.input_sha256, altered, first.axes, None)
        with self.assertRaisesRegex(RetrievalError, "mixed encoder"):
            project_predictions(self.requests, preds)

    def test_projection_rejects_bad_binding(self):
        from spectral_public.adapter import EncodePrediction, AdapterError
        preds = list(self.predictions)
        first = preds[0]
        preds[0] = EncodePrediction(first.item_id, "a" * 64, first.encoder, first.axes, None)
        with self.assertRaises(AdapterError):
            project_predictions(self.requests, preds)

    def test_cli_p2_corpus_writes_new_file_only(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "projected.json"
            args = ["p2-corpus", str(ROOT / "examples/p2_requests.json"),
                    str(ROOT / "examples/p2_predictions.json"), "--out", str(out)]
            with redirect_stdout(StringIO()) as stdout:
                self.assertEqual(main(args), 0)
            self.assertEqual(len(json.loads(out.read_text(encoding="utf-8"))), 8)
            with redirect_stderr(StringIO()) as stderr:
                self.assertEqual(main(args), 2)
            self.assertIn("File exists", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
