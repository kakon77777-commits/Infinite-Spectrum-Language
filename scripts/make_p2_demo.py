"""Generate deliberately synthetic, non-scientific ISL P2 interchange fixtures."""
from __future__ import annotations
import json
from pathlib import Path

from spectral_public.adapter import EncodeRequest, EncoderInfo, EncodePrediction, REQUEST_PROFILE, PREDICTION_PROFILE
from spectral_public.core import Interval
from spectral_public.evaluation import EVALUATION_PROFILE

OUT = Path(__file__).resolve().parents[1] / "examples"
CASES = [
    # item ID, text, explicit context, context group, invented gold (joy, calm), invented predicted midpoints
    ("demo01", "今天好冷。", "在室外等公車，寒風很強", "daily", (.20, .30), (.45, .45)),
    ("demo02", "今天好冷。", "在炎熱天氣開玩笑說很冷", "ironic", (.68, .58), (.45, .45)),
    ("demo03", "這結果太棒了。", "朋友考試通過", "daily", (.91, .70), (.82, .72)),
    ("demo04", "這結果太棒了。", "程式再次崩潰時反諷", "ironic", (.17, .26), (.82, .72)),
    ("demo05", "系統保持穩定。", "監測伺服器運行", "technical", (.48, .88), (.50, .75)),
    ("demo06", "系統保持穩定。", "小說角色描述情緒", "daily", (.55, .73), (.50, .75)),
    ("demo07", "我需要一些時間。", "準備嚴肅報告", "technical", (.33, .57), (.45, .55)),
    ("demo08", "我需要一些時間。", "週末想休息", "daily", (.71, .79), (.45, .55)),
]


def write(filename: str, obj: dict) -> None:
    (OUT / filename).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    requests, predictions, labels = [], [], []
    info = EncoderInfo("synthetic-replay-baseline", "0.0-demo", "demo-run-001", "synthetic-offline-fixture")
    for item_id, text, context, group, truth, guess in CASES:
        r = EncodeRequest(item_id, text, context, group, ("joy", "calm"))
        requests.append({"item_id": item_id, "text": text, "context": context,
                         "context_group": group, "axes": list(r.axes)})
        intervals = {axis: Interval(max(0.0, round(mid - .10, 3)), min(1.0, round(mid + .10, 3)))
                     for axis, mid in zip(r.axes, guess)}
        predictions.append(EncodePrediction(item_id, r.input_sha256, info, intervals, None).to_json())
        labels.append({"item_id": item_id, "values": dict(zip(r.axes, truth)),
                       "annotation_source": "invented-demonstration-value"})
    write("p2_requests.json", {"profile": REQUEST_PROFILE, "items": requests})
    write("p2_predictions.json", {"profile": PREDICTION_PROFILE, "predictions": predictions})
    write("p2_heldout.json", {"profile": EVALUATION_PROFILE, "split": "heldout",
                               "annotation_protocol": "SYNTHETIC DEMO; labels not independently annotated or validated",
                               "labels": labels})


if __name__ == "__main__":
    main()
