from __future__ import annotations

import json

import pytest

from daxlab.runtime.candidate_pipeline import Cand001PipelineState
from daxlab.runtime.candidate_signal import Cand001SignalState
from daxlab.strategies.cand001 import Cand001PipelineStateCodec


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_codec_rejects_non_finite_prices_when_encoding(value: float) -> None:
    codec = Cand001PipelineStateCodec()
    state = Cand001PipelineState(
        signal=Cand001SignalState(
            session_date="2026-09-11",
            or_high=value,
            or_low=98.0,
            or_slots=("09:00",),
        )
    )

    with pytest.raises(ValueError, match="signal.or_high must be finite"):
        codec.encode(state)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_codec_rejects_non_finite_prices_when_decoding(token: str) -> None:
    codec = Cand001PipelineStateCodec()
    payload = {
        "schema_version": "DAXLAB_CAND001_PIPELINE_STATE_V1",
        "signal": {
            "session_date": "2026-09-11",
            "or_high": 103.0,
            "or_low": 98.0,
            "or_slots": ["09:00", "09:05", "09:10"],
            "last_close_time_utc": "2026-09-11T07:15:00+00:00",
        },
        "admission": {
            "session_date": "2026-09-11",
            "trades_admitted": 1,
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    encoded = encoded.replace("103.0", token, 1).encode("utf-8")

    with pytest.raises(ValueError, match="signal.or_high must be finite"):
        codec.decode(encoded)
