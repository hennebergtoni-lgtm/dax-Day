from dataclasses import replace
from datetime import date, timedelta

import pytest

from daxlab.research.cand001_oos_walk_forward import (
    ECONOMIC_CLAIM,
    EVIDENCE_CLASS,
    OOS_ROLE,
    SELECTION_POLICY,
    TRAIN_ROLE,
    Cand001OosResultIdentity,
    Cand001OosWindow,
    build_cand001_oos_contract,
    build_cand001_oos_result_identity,
    build_cand001_oos_windows,
)
from daxlab.runtime.candidate_config import Cand001Config


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
REPLAY_SHA = "a" * 64


def _days(count: int) -> list[date]:
    start = date(2014, 1, 1)
    return [start + timedelta(days=index) for index in range(count)]


def test_contract_freezes_candidate_chronology_costs_and_no_tuning() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    again = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    config = Cand001Config()
    identity = config.product_identity()

    assert contract == again
    assert contract.fingerprint == again.fingerprint
    assert contract.candidate_id == "CAND-001"
    assert contract.product_core_version == identity.core_version
    assert contract.config_fingerprint == identity.config_fingerprint
    assert (contract.train_days, contract.oos_days, contract.step_days) == (45, 20, 20)
    assert contract.cost_stresses == (
        ("normal", 1.0),
        ("stress_1.5x", 1.5),
        ("stress_2x", 2.0),
    )
    assert contract.selection_policy == SELECTION_POLICY
    assert contract.train_role == TRAIN_ROLE == "CONTEXT_ONLY_NO_SELECTION"
    assert contract.oos_role == OOS_ROLE == "MEASUREMENT_ONLY"
    assert contract.evidence_class == EVIDENCE_CLASS
    assert contract.economic_claim == ECONOMIC_CLAIM
    assert contract.execution_capability == "NONE"
    assert contract.order_execution_enabled is False


def test_1673_days_yield_exactly_81_frozen_walk_forward_windows() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    days = _days(1673)

    windows = build_cand001_oos_windows(days, contract)

    assert len(windows) == 81
    assert windows[0].number == 1
    assert windows[0].train_start == days[0].isoformat()
    assert windows[0].train_end == days[44].isoformat()
    assert windows[0].oos_start == days[45].isoformat()
    assert windows[0].oos_end == days[64].isoformat()
    assert windows[0].train_days == 45
    assert windows[0].oos_days == 20
    assert windows[1].train_start == days[20].isoformat()
    assert windows[1].oos_start == days[65].isoformat()
    assert windows[-1].number == 81
    assert windows[-1].train_start == days[1600].isoformat()
    assert windows[-1].oos_end == days[1664].isoformat()
    assert all(window.contract_fingerprint == contract.fingerprint for window in windows)
    assert len({window.window_fingerprint for window in windows}) == 81


def test_windows_are_deterministic_and_train_oos_are_chronologically_disjoint() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    days = _days(200)

    first = build_cand001_oos_windows(days, contract)
    second = build_cand001_oos_windows(days, contract)

    assert first == second
    for window in first:
        assert date.fromisoformat(window.train_end) < date.fromisoformat(window.oos_start)
        assert window.train_days == 45
        assert window.oos_days == 20


def test_window_builder_rejects_duplicate_or_unsorted_days() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    days = _days(70)

    duplicated = list(days)
    duplicated[10] = duplicated[9]
    with pytest.raises(ValueError, match="unique"):
        build_cand001_oos_windows(duplicated, contract)

    unsorted = list(days)
    unsorted[10], unsorted[11] = unsorted[11], unsorted[10]
    with pytest.raises(ValueError, match="strictly chronological"):
        build_cand001_oos_windows(unsorted, contract)


def test_contract_rejects_identity_chronology_cost_or_execution_drift() -> None:
    base = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)

    with pytest.raises(ValueError, match="dataset_fingerprint"):
        replace(base, dataset_fingerprint="x" * 64)
    with pytest.raises(ValueError, match="config_fingerprint"):
        replace(base, config_fingerprint="x" * 64)
    with pytest.raises(ValueError, match="45/20/20"):
        replace(base, train_days=46)
    with pytest.raises(ValueError, match="cost stresses"):
        replace(base, cost_stresses=(("normal", 1.0),))
    with pytest.raises(ValueError, match="selection/tuning"):
        replace(base, train_role="SELECT_BEST")
    with pytest.raises(ValueError, match="cannot authorize execution"):
        replace(base, order_execution_enabled=True)


def test_window_identity_rejects_invalid_sha_or_overlapping_chronology() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    window = build_cand001_oos_windows(_days(70), contract)[0]

    with pytest.raises(ValueError, match="contract_fingerprint"):
        replace(window, contract_fingerprint="z" * 64)
    with pytest.raises(ValueError, match="window_fingerprint"):
        replace(window, window_fingerprint="short")
    with pytest.raises(ValueError, match="train then OOS"):
        replace(window, oos_start=window.train_end)


def test_result_identity_is_deterministic_cost_bound_and_non_executable() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    window = build_cand001_oos_windows(_days(70), contract)[0]

    normal = build_cand001_oos_result_identity(
        contract=contract,
        window=window,
        cost_model="normal",
        replay_report_fingerprint=REPLAY_SHA,
    )
    same = build_cand001_oos_result_identity(
        contract=contract,
        window=window,
        cost_model="normal",
        replay_report_fingerprint=REPLAY_SHA,
    )
    stressed = build_cand001_oos_result_identity(
        contract=contract,
        window=window,
        cost_model="stress_1.5x",
        replay_report_fingerprint=REPLAY_SHA,
    )

    assert normal == same
    assert normal.cost_multiplier == 1.0
    assert stressed.cost_multiplier == 1.5
    assert stressed.result_fingerprint != normal.result_fingerprint
    assert normal.evidence_class == EVIDENCE_CLASS
    assert normal.economic_claim == ECONOMIC_CLAIM
    assert normal.execution_capability == "NONE"
    assert normal.order_execution_enabled is False


def test_result_identity_rejects_unknown_cost_wrong_contract_or_bad_sha() -> None:
    contract = build_cand001_oos_contract(dataset_fingerprint=DATASET_SHA)
    window = build_cand001_oos_windows(_days(70), contract)[0]

    with pytest.raises(ValueError, match="cost_model"):
        build_cand001_oos_result_identity(
            contract=contract,
            window=window,
            cost_model="stress_99x",
            replay_report_fingerprint=REPLAY_SHA,
        )
    with pytest.raises(ValueError, match="replay_report_fingerprint"):
        build_cand001_oos_result_identity(
            contract=contract,
            window=window,
            cost_model="normal",
            replay_report_fingerprint="z" * 64,
        )

    other_contract = build_cand001_oos_contract(dataset_fingerprint="b" * 64)
    with pytest.raises(ValueError, match="not bound"):
        build_cand001_oos_result_identity(
            contract=other_contract,
            window=window,
            cost_model="normal",
            replay_report_fingerprint=REPLAY_SHA,
        )


def test_result_dataclass_rejects_non_hex_fingerprints_and_execution_drift() -> None:
    with pytest.raises(ValueError, match="window_fingerprint"):
        Cand001OosResultIdentity(
            window_fingerprint="z" * 64,
            cost_model="normal",
            cost_multiplier=1.0,
            replay_report_fingerprint=REPLAY_SHA,
            result_fingerprint="b" * 64,
        )

    with pytest.raises(ValueError, match="cannot authorize execution"):
        Cand001OosResultIdentity(
            window_fingerprint="a" * 64,
            cost_model="normal",
            cost_multiplier=1.0,
            replay_report_fingerprint=REPLAY_SHA,
            result_fingerprint="b" * 64,
            order_execution_enabled=True,
        )


def test_window_dataclass_rejects_invalid_number() -> None:
    with pytest.raises(ValueError, match="positive"):
        Cand001OosWindow(
            number=0,
            train_start="2014-01-01",
            train_end="2014-02-14",
            oos_start="2014-02-15",
            oos_end="2014-03-06",
            train_days=45,
            oos_days=20,
            contract_fingerprint="a" * 64,
            window_fingerprint="b" * 64,
        )
