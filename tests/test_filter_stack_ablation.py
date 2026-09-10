from __future__ import annotations

import pytest

from daxlab.research.filter_stack_ablation import evaluate_filter_stack


def test_redundant_filter_has_zero_active_effect() -> None:
    result = evaluate_filter_stack(
        [1.0, -1.0, 2.0, -0.5],
        [
            ("A", [True, False, True, True]),
            ("B", [True, False, True, True]),
        ],
    )
    first, second = result.stages
    assert first.active_effect_count == 1
    assert first.redundant_in_stack is False
    assert first.incremental.net_filter_value_r == pytest.approx(1.0)
    assert second.active_effect_count == 0
    assert second.redundant_in_stack is True
    assert second.incremental.net_filter_value_r == pytest.approx(0.0)
    assert result.final_kept_trades == 3


def test_later_filter_can_destroy_value_after_good_filter() -> None:
    result = evaluate_filter_stack(
        [1.0, -1.0, 2.0, -0.5],
        [
            ("LOSS_AVOID", [True, False, True, True]),
            ("WINNER_KILL", [False, True, True, True]),
        ],
    )
    first, second = result.stages
    assert first.incremental.delta_total_r == pytest.approx(1.0)
    assert second.incremental.delta_total_r == pytest.approx(-1.0)
    assert second.incremental.missed_profit_r == pytest.approx(1.0)
    assert result.final_delta_r_vs_baseline == pytest.approx(0.0)


def test_stack_order_changes_incremental_evidence() -> None:
    baseline = [1.0, -1.0, 2.0, -0.5]
    a = [True, False, True, True]
    c = [False, True, True, True]
    first = evaluate_filter_stack(baseline, [("A", a), ("C", c)])
    second = evaluate_filter_stack(baseline, [("C", c), ("A", a)])
    assert first.stack_sha256 != second.stack_sha256
    assert first.stages[0].incremental.diagnostic_sha256 != second.stages[0].incremental.diagnostic_sha256


def test_all_trades_blocked_is_explicit() -> None:
    result = evaluate_filter_stack(
        [1.0, -1.0, 0.5],
        [
            ("A", [False, True, True]),
            ("B", [True, False, False]),
        ],
    )
    assert result.final_kept_trades == 0
    assert result.final_survival_ratio == pytest.approx(0.0)
    assert result.all_trades_blocked is True
    payload = result.to_payload()
    assert payload["automatic_keep_drop_decision"] is None
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_duplicate_ids_and_bad_masks_fail_closed() -> None:
    with pytest.raises(ValueError, match="duplicate filter_id"):
        evaluate_filter_stack(
            [1.0, -1.0],
            [("A", [True, False]), ("A", [False, True])],
        )
    with pytest.raises(ValueError, match="match baseline_r length"):
        evaluate_filter_stack([1.0, -1.0], [("A", [True])])
