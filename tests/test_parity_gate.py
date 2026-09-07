from daxlab.reference.parity import PRE_GATE_REFERENCE, MetricSnapshot, compare_metrics


def test_known_trade_bearing_pre_gate_is_exact() -> None:
    result = compare_metrics(
        MetricSnapshot(trades=14, return_r=3.9351648669, pf=1.5556035886),
        PRE_GATE_REFERENCE,
    )
    assert result.passed
    assert result.mismatches == ()


def test_parity_rejects_trade_count_drift() -> None:
    result = compare_metrics(
        MetricSnapshot(trades=13, return_r=3.9351648669, pf=1.5556035886),
        PRE_GATE_REFERENCE,
    )
    assert not result.passed
    assert result.mismatches[0].startswith("trades:")


def test_parity_rejects_tiny_but_material_return_drift() -> None:
    result = compare_metrics(
        MetricSnapshot(trades=14, return_r=3.935164, pf=1.5556035886),
        PRE_GATE_REFERENCE,
    )
    assert not result.passed
