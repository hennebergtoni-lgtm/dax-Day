from datetime import date

import pytest

from daxlab.data.recovery import RecoveryIdentity
from daxlab.runtime import full_reference
from daxlab.runtime.readiness import ReadinessSnapshot
from daxlab.runtime.v112_bridge import V112DayResult


def snapshot(**overrides: object) -> ReadinessSnapshot:
    values: dict[str, object] = {
        "ci_green": True,
        "dataset_verified": True,
        "engine_verified": True,
        "database_verified": True,
        "technical_replay_verified": True,
        "audited_bundle_available": True,
        "full_reference_replay_verified": False,
        "execution_boundary_verified": False,
        "dataset_identity": RecoveryIdentity.HASH_VERIFIED,
    }
    values.update(overrides)
    return ReadinessSnapshot(**values)  # type: ignore[arg-type]


def test_structural_only_data_blocks_full_reference_replay() -> None:
    with pytest.raises(RuntimeError, match="DATASET_IDENTITY_NOT_HASH_VERIFIED"):
        full_reference.run_guarded_full_reference_replay(
            object(),
            (object(),),  # type: ignore[arg-type]
            object(),
            snapshot(dataset_identity=RecoveryIdentity.STRUCTURAL_MATCH),
        )


def test_guarded_replay_requires_nonempty_candles() -> None:
    with pytest.raises(ValueError, match="requires candles"):
        full_reference.run_guarded_full_reference_replay(
            object(),
            (),
            object(),
            snapshot(),
        )


def test_guarded_replay_checks_parity_and_rerun_determinism(monkeypatch: pytest.MonkeyPatch) -> None:
    results = (V112DayResult(day=date(2026, 1, 5), outcome=[]),)
    replay_calls = 0

    def fake_historical(*args: object, **kwargs: object) -> tuple[V112DayResult, ...]:
        return results

    def fake_replay(*args: object, **kwargs: object) -> tuple[V112DayResult, ...]:
        nonlocal replay_calls
        replay_calls += 1
        return results

    monkeypatch.setattr(full_reference, "run_historical_days", fake_historical)
    monkeypatch.setattr(full_reference, "run_replay_days", fake_replay)

    output = full_reference.run_guarded_full_reference_replay(
        object(),
        (object(),),  # type: ignore[arg-type]
        object(),
        snapshot(),
    )

    assert output.days == 1
    assert output.historical_fingerprint == output.replay_fingerprint
    assert replay_calls == 2
