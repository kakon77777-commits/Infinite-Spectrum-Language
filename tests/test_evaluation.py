"""Held-out scoring must fail closed on corruption and disclose metric limitations."""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from spectral_public.adapter import AdapterError, EncodePrediction, load_requests, load_predictions
from spectral_public.evaluation import HeldoutLabel, evaluate, load_heldout
from spectral_public.cli import main

BASE = Path(__file__).resolve().parents[1]


class TestEvaluation(unittest.TestCase):
    def setUp(self):
        self.requests = load_requests(BASE / "examples/p2_requests.json")
        self.predictions = load_predictions(BASE / "examples/p2_predictions.json")
        self.protocol, self.labels = load_heldout(BASE / "examples/p2_heldout.json")

    def test_metrics_and_groups(self):
        report = evaluate(self.requests, self.predictions, self.labels, self.protocol)
        self.assertEqual(report["request_count"], 8)
        self.assertEqual(report["scored_axis_points"], 16)
        self.assertEqual(report["overall"]["count"], 16)
        self.assertIn("ironic", report["by_context_group"])
        self.assertIn("technical", report["by_context_group"])
        self.assertTrue(0 <= report["overall"]["point_coverage"] <= 1)
        self.assertIn("NOT probability calibration", report["limitations"][1])
        self.assertGreater(report["by_context_group"]["ironic"]["midpoint_mae"],
                           report["by_context_group"]["technical"]["midpoint_mae"])

    def test_labels_match_requests(self):
        with self.assertRaisesRegex(AdapterError, "exactly"):
            evaluate(self.requests, self.predictions, self.labels[1:], self.protocol)

    def test_wrong_axes_rejected(self):
        bad = HeldoutLabel(self.labels[0].item_id, {"joy": .5}, "test")
        with self.assertRaisesRegex(AdapterError, "axes"):
            evaluate(self.requests, self.predictions, [bad] + self.labels[1:], self.protocol)

    def test_bad_labels_rejected(self):
        for v in [True, 1.1, float('nan')]:
            with self.assertRaises(AdapterError):
                HeldoutLabel.from_json({"item_id":"x", "values":{"joy":v}, "annotation_source":"test"})

    def test_mixed_encoder_run_rejected(self):
        raw = self.predictions[0].to_json()
        raw["encoder"]["run_id"] = "different"
        with self.assertRaisesRegex(AdapterError, "only one encoder"):
            evaluate(self.requests, [EncodePrediction.from_json(raw)] + self.predictions[1:], self.labels, self.protocol)

    def test_abstentions_are_counted_not_silently_scored(self):
        raw = self.predictions[0].to_json()
        raw["axes"] = {}
        raw["abstain_reason"] = "insufficient context"
        report = evaluate(self.requests, [EncodePrediction.from_json(raw)] + self.predictions[1:], self.labels, self.protocol)
        self.assertEqual(report["abstained_count"], 1)
        self.assertEqual(report["scored_axis_points"], 14)
        self.assertEqual(report["abstention_reasons"]["insufficient context"], 1)

    def test_all_abstentions_no_division_by_zero(self):
        rows = []
        for pred in self.predictions:
            raw = pred.to_json()
            raw["axes"] = {}
            raw["abstain_reason"] = "unsupported"
            rows.append(EncodePrediction.from_json(raw))
        report = evaluate(self.requests, rows, self.labels, self.protocol)
        self.assertIsNone(report["overall"]["point_coverage"])
        self.assertEqual(report["abstained_count"], 8)

    def test_heldout_only(self):
        data = json.loads((BASE / "examples/p2_heldout.json").read_text(encoding="utf-8"))
        data["split"] = "train"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"bad.json"
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(AdapterError, "heldout"):
                load_heldout(path)

    def test_cli_evaluate(self):
        with redirect_stdout(io.StringIO()) as buffer:
            code = main(["evaluate", str(BASE / "examples/p2_requests.json"),
                         str(BASE / "examples/p2_predictions.json"),
                         str(BASE / "examples/p2_heldout.json")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())["profile"], "isl-evaluation-report/0.2")


if __name__ == "__main__":
    unittest.main()
