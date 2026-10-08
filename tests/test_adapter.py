"""P2 adapter strictness, provenance, context binding and CLI tests."""
import copy
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest

from spectral_public.adapter import (AdapterError, EncodeRequest, EncoderInfo, EncodePrediction,
                                     FixtureReplayEncoder, abstention_template, load_requests,
                                     load_predictions, validate_pair)
from spectral_public.cli import main

BASE = Path(__file__).resolve().parents[1]
REQUESTS = BASE / "examples/p2_requests.json"
PREDICTIONS = BASE / "examples/p2_predictions.json"


class TestP2Adapter(unittest.TestCase):
    def setUp(self):
        self.requests = load_requests(REQUESTS)
        self.predictions = load_predictions(PREDICTIONS)

    def test_offline_fixture_bound_exactly(self):
        validate_pair(self.requests, self.predictions)
        replay = FixtureReplayEncoder(self.requests, self.predictions)
        self.assertEqual(replay.encode(self.requests[0]), self.predictions[0])

    def test_deterministic_input_hash(self):
        a = self.requests[0]
        b = EncodeRequest(a.item_id, a.text, a.context, a.context_group, a.axes)
        self.assertEqual(a.input_sha256, b.input_sha256)
        self.assertEqual(len(a.input_sha256), 64)

    def test_context_is_bound_to_hash(self):
        r = self.requests[0]
        changed = EncodeRequest(r.item_id, r.text, "changed", r.context_group, r.axes)
        self.assertNotEqual(r.input_sha256, changed.input_sha256)
        with self.assertRaisesRegex(AdapterError, "digest mismatch"):
            validate_pair([changed] + self.requests[1:], self.predictions)

    def test_axis_order_is_bound(self):
        r = self.requests[0]
        changed = EncodeRequest(r.item_id, r.text, r.context, r.context_group, tuple(reversed(r.axes)))
        self.assertNotEqual(r.input_sha256, changed.input_sha256)

    def test_changed_record_cannot_replay(self):
        r = self.requests[0]
        replay = FixtureReplayEncoder(self.requests, self.predictions)
        with self.assertRaises(AdapterError):
            replay.encode(EncodeRequest(r.item_id, r.text + "!", r.context, r.context_group, r.axes))

    def test_missing_and_extra_predictions_rejected(self):
        with self.assertRaisesRegex(AdapterError, "exactly"):
            validate_pair(self.requests, self.predictions[1:])
        with self.assertRaisesRegex(AdapterError, "exactly"):
            validate_pair(self.requests[1:], self.predictions)

    def test_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(AdapterError, "duplicate"):
            validate_pair(self.requests, self.predictions + self.predictions[:1])

    def test_wrong_axis_set_rejected(self):
        raw = self.predictions[0].to_json()
        del raw["axes"]["joy"]
        wrong = EncodePrediction.from_json(raw)
        with self.assertRaisesRegex(AdapterError, "axes"):
            validate_pair(self.requests, [wrong] + self.predictions[1:])

    def test_invalid_range_rejected(self):
        raw = self.predictions[0].to_json()
        raw["axes"]["joy"]["lower"] = 1.3
        with self.assertRaisesRegex(AdapterError, "interval"):
            EncodePrediction.from_json(raw)

    def test_boolean_and_nan_rejected(self):
        for value in [True, float('nan'), float('inf')]:
            raw = self.predictions[0].to_json()
            raw["axes"]["joy"]["lower"] = value
            with self.assertRaises(AdapterError):
                EncodePrediction.from_json(raw)

    def test_abstention_has_no_axes(self):
        info = EncoderInfo("test", "1", "run", "local")
        raw = abstention_template(self.requests, info)
        self.assertEqual(len(raw["predictions"]), 8)
        self.assertEqual(raw["predictions"][0]["axes"], {})
        wrong = copy.deepcopy(raw["predictions"][0])
        wrong["axes"] = self.predictions[0].to_json()["axes"]
        with self.assertRaisesRegex(AdapterError, "abstaining"):
            EncodePrediction.from_json(wrong)

    def test_invalid_utf8_surrogate_rejected(self):
        raw = {"item_id":"x", "text":"\ud800", "context":"t", "context_group":"x", "axes":["joy"]}
        with self.assertRaisesRegex(AdapterError, "UTF-8"):
            EncodeRequest.from_json(raw)

    def test_axes_duplicate_rejected(self):
        raw = {"item_id":"x", "text":"t", "context":"t", "context_group":"x", "axes":["joy","joy"]}
        with self.assertRaisesRegex(AdapterError, "unique"):
            EncodeRequest.from_json(raw)

    def test_cli_adapter_check(self):
        with redirect_stdout(io.StringIO()) as buffer:
            code = main(["adapter-check", str(REQUESTS), str(PREDICTIONS)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue())["predicted"], 8)

    def test_cli_template_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            target = str(Path(d)/"new.json")
            args = ["adapter-template", str(REQUESTS), "--out", target,
                    "--encoder-name", "manual", "--encoder-version", "1", "--run-id", "run1"]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            self.assertTrue(Path(target).exists())
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 2)
            self.assertEqual(len(load_predictions(target)), 8)

    def test_unrecognized_prediction_metadata_rejected(self):
        raw = self.predictions[0].to_json()
        raw["secret"] = "not allowed"
        with self.assertRaises(AdapterError):
            EncodePrediction.from_json(raw)


if __name__ == "__main__":
    unittest.main()
