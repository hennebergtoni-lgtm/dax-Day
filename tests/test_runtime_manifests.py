from datetime import UTC, datetime

import pytest

from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import DecisionRecord, FinalAction
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest, assert_run_manifest_matches


def test_run_manifest_is_deterministic() -> None:
    first = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"rr": 1.5, "or": 15},
        mode=RuntimeMode.REPLAY,
    )
    second = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"or": 15, "rr": 1.5},
        mode=RuntimeMode.REPLAY,
    )
    assert first == second
    assert_run_manifest_matches(first, second)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dataset", "other-data", "dataset fingerprint drift"),
        ("engine", "other-engine", "engine fingerprint drift"),
        ("config", {"rr": 2.0}, "config fingerprint drift"),
        ("mode", RuntimeMode.HISTORICAL, "mode drift"),
    ],
)
def test_run_manifest_aborts_on_identity_drift(field: str, value: object, message: str) -> None:
    expected = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"rr": 1.5},
        mode=RuntimeMode.REPLAY,
    )
    observed = RunManifest.build(
        dataset_fingerprint=value if field == "dataset" else "data",  # type: ignore[arg-type]
        engine_fingerprint=value if field == "engine" else "engine",  # type: ignore[arg-type]
        config=value if field == "config" else {"rr": 1.5},
        mode=value if field == "mode" else RuntimeMode.REPLAY,  # type: ignore[arg-type]
    )
    with pytest.raises(RuntimeError, match=message):
        assert_run_manifest_matches(expected, observed)


def test_decision_log_manifest_counts_no_trade_records() -> None:
    event_time = datetime(2026, 1, 2, 9, 5, tzinfo=UTC)
    no_trade = DecisionRecord.build(
        event_time=event_time,
        data_fingerprint="data",
        regime="normal",
        structure="none",
        setup="none",
        filter_results={},
        blockers=("NO_SETUP",),
        risk_result="BLOCKED",
        config={"rr": 1.5},
        core_version="V11.2",
        final_action=FinalAction.NO_TRADE,
    )
    manifest = DecisionLogManifest.build((no_trade,))
    assert manifest.decisions == 1
    assert manifest.trades == 0
    assert manifest.no_trades == 1
    assert len(manifest.decision_ids_fingerprint) == 64
