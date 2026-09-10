import pytest

from daxlab.research.filter_overlap_redundancy import FilterMask, evaluate_filter_overlap


def test_identical_block_sets_have_full_overlap():
    report = evaluate_filter_overlap(
        [
            FilterMask("A", (True, False, True, False)),
            FilterMask("B", (True, False, True, False)),
        ]
    )
    pair = report.pairs[0]
    assert pair.jaccard_blocked == 1.0
    assert pair.containment_a_in_b == 1.0
    assert pair.containment_b_in_a == 1.0


def test_disjoint_block_sets_have_zero_overlap():
    report = evaluate_filter_overlap(
        [
            FilterMask("A", (False, True, True, True)),
            FilterMask("B", (True, False, True, True)),
        ]
    )
    pair = report.pairs[0]
    assert pair.jaccard_blocked == 0.0
    assert pair.containment_a_in_b == 0.0
    assert pair.containment_b_in_a == 0.0


def test_asymmetric_containment_is_visible():
    report = evaluate_filter_overlap(
        [
            FilterMask("A", (False, False, True, True)),
            FilterMask("B", (False, True, True, True)),
        ]
    )
    pair = report.pairs[0]
    assert pair.blocked_intersection == 1
    assert pair.containment_a_in_b == 0.5
    assert pair.containment_b_in_a == 1.0


def test_no_blocked_trades_is_not_false_redundancy():
    report = evaluate_filter_overlap(
        [
            FilterMask("A", (True, True, True)),
            FilterMask("B", (True, True, True)),
        ]
    )
    pair = report.pairs[0]
    assert pair.blocked_union == 0
    assert pair.jaccard_blocked == 0.0
    assert pair.containment_a_in_b == 0.0
    assert pair.containment_b_in_a == 0.0


def test_hash_changes_when_mask_changes():
    first = evaluate_filter_overlap(
        [FilterMask("A", (True, False)), FilterMask("B", (False, True))]
    )
    second = evaluate_filter_overlap(
        [FilterMask("A", (True, True)), FilterMask("B", (False, True))]
    )
    assert first.report_sha256 != second.report_sha256


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        evaluate_filter_overlap([FilterMask("A", (True,))])
    with pytest.raises(ValueError):
        evaluate_filter_overlap(
            [FilterMask("A", (True, False)), FilterMask("A", (True, False))]
        )
    with pytest.raises(ValueError):
        evaluate_filter_overlap(
            [FilterMask("A", (True,)), FilterMask("B", (True, False))]
        )
