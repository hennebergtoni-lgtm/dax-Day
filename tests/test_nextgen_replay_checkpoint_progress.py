from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

import pytest

from daxlab.state.replay_checkpoint import (
    CheckpointCompatibilityError,
    assert_checkpoint_compatible,
    build_product_checkpoint,
)


UTC = timezone.utc


def _sha(value: bytes) -> str:
    return sha256(value).hexdigest()


def _checkpoint():
    return build_product_checkpoint(
        engine_version="NEXTGEN_REPLAY_V1",
        run_fingerprint=_sha(b"run"),
        strategy_id="SYNTHETIC-PROGRESS",
        strategy_version="1",
        strategy_fingerprint=_sha(b"strategy"),
        config_fingerprint=_sha(b"config"),
        source_commit="1" * 40,
        instrument_id="DAX.CFD",
        timeframe="M5",
        total_event_count=5,
        input_fingerprint=_sha(b"input"),
        processed_event_count=3,
        last_event_time=datetime(2026, 9, 10, 8, 15, tzinfo=UTC),
        last_decision_id=_sha(b"decision-3"),
        decision_ids_fingerprint=_sha(b"decisions-through-3"),
        state_codec_id="synthetic-json-v1",
        strategy_state=b'{"processed":3}',
    )


def _compatibility_kwargs() -> dict[str, object]:
    item = _checkpoint()
    return {
        "engine_version": item.engine_version,
        "run_fingerprint": item.run_fingerprint,
        "strategy_id": item.strategy_id,
        "strategy_version": item.strategy_version,
        "strategy_fingerprint": item.strategy_fingerprint,
        "config_fingerprint": item.config_fingerprint,
        "source_commit": item.source_commit,
        "instrument_id": item.instrument_id,
        "timeframe": item.timeframe,
        "total_event_count": item.total_event_count,
        "input_fingerprint": item.input_fingerprint,
        "state_codec_id": item.state_codec_id,
    }


def test_resume_accepts_checkpoint_at_or_beyond_required_position() -> None:
    item = _checkpoint()
    expected = _compatibility_kwargs()

    assert_checkpoint_compatible(
        item,
        **expected,  # type: ignore[arg-type]
        minimum_processed_event_count=3,
    )
    assert_checkpoint_compatible(
        item,
        **expected,  # type: ignore[arg-type]
        minimum_processed_event_count=2,
    )


def test_resume_rejects_checkpoint_position_regression() -> None:
    item = _checkpoint()
    expected = _compatibility_kwargs()

    with pytest.raises(
        CheckpointCompatibilityError,
        match="processed_event_count regression",
    ):
        assert_checkpoint_compatible(
            item,
            **expected,  # type: ignore[arg-type]
            minimum_processed_event_count=4,
        )


def test_required_resume_position_must_be_valid_integer_within_run() -> None:
    item = _checkpoint()
    expected = _compatibility_kwargs()

    with pytest.raises(ValueError, match="must be integer"):
        assert_checkpoint_compatible(
            item,
            **expected,  # type: ignore[arg-type]
            minimum_processed_event_count=True,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="outside run bounds"):
        assert_checkpoint_compatible(
            item,
            **expected,  # type: ignore[arg-type]
            minimum_processed_event_count=6,
        )
