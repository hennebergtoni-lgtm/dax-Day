import json
from pathlib import Path


def test_v10_does_not_change_frozen_v112_reference_identity() -> None:
    root = Path(__file__).resolve().parents[1]
    ref = json.loads((root / "research/V112_REFERENCE_V1/reference_result.json").read_text())
    assert ref["experiment_id"] == "V112_REFERENCE_V1"
    assert ref["strategy"] == "V11.2"
    assert ref["strategy_changed"] is False
    assert ref["dataset"]["session_m5_rows"] == 172319
    assert ref["dataset"]["valid_session_days"] == 1673
    assert ref["dataset"]["session_ohlc_sha256"] == (
        "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
    )
    assert ref["engine"]["variants"] == 144
    assert ref["walk_forward"]["windows"] == 81
    assert ref["results"]["normal"]["oos_trades"] == 856
