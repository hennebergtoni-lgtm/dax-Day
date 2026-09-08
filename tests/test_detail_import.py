from daxlab.detail_import import berlin_wall_clock_to_utc, plan_detail_rows


def test_wf_metrics_identity_is_stable() -> None:
    row = {
        "wf": 1,
        "cost": "normal",
        "variant_index": 120,
        "trades": 12,
        "return_r": 2.5,
        "pf": 1.4,
        "avg_r": 0.2,
        "max_dd_r": -3.0,
    }
    first = plan_detail_rows(experiment_key="V112_REFERENCE_V1", detail_kind="WF_METRICS", rows=[row])
    second = plan_detail_rows(experiment_key="V112_REFERENCE_V1", detail_kind="WF_METRICS", rows=[dict(row)])
    assert first == second
    assert len(first[0].source_row_id) == 64
    assert len(first[0].payload_sha256) == 64


def test_duplicate_source_identity_fails_closed() -> None:
    row = {
        "wf": 1,
        "cost": "normal",
        "variant_index": 120,
        "trades": 12,
        "return_r": 2.5,
        "pf": 1.4,
        "avg_r": 0.2,
        "max_dd_r": -3.0,
    }
    try:
        plan_detail_rows(
            experiment_key="V112_REFERENCE_V1", detail_kind="WF_METRICS", rows=[row, row]
        )
    except ValueError as exc:
        assert "duplicate source_row_id" in str(exc)
    else:
        raise AssertionError("duplicate row must fail closed")


def test_conflicting_duplicate_source_identity_fails_closed() -> None:
    a = {
        "wf": 1,
        "cost": "normal",
        "variant_index": 120,
        "trades": 12,
        "return_r": 2.5,
        "pf": 1.4,
        "avg_r": 0.2,
        "max_dd_r": -3.0,
    }
    b = dict(a)
    b["return_r"] = 99.0
    try:
        plan_detail_rows(
            experiment_key="V112_REFERENCE_V1", detail_kind="WF_METRICS", rows=[a, b]
        )
    except ValueError as exc:
        assert "conflicting duplicate" in str(exc)
    else:
        raise AssertionError("conflicting duplicate must fail closed")


def test_trade_wall_clock_is_localized_to_berlin_then_utc() -> None:
    assert berlin_wall_clock_to_utc("2019-07-01 10:05:00", "entry_time") == "2019-07-01T08:05:00+00:00"
    assert berlin_wall_clock_to_utc("2019-01-02 10:05:00", "entry_time") == "2019-01-02T09:05:00+00:00"


def test_trade_plan_rejects_invalid_side() -> None:
    row = {
        "wf": 1,
        "variant_index": 120,
        "date": "2014-02-17",
        "r": -1.0,
        "side": "BUYISH",
        "entry": 100.0,
        "exit": 99.0,
        "reason": "stop",
        "entry_time": "2014-02-17 10:05:00",
        "exit_time": "2014-02-17 10:45:00",
        "mfe_r": 0.4,
        "mae_r": 1.1,
    }
    try:
        plan_detail_rows(experiment_key="V112_REFERENCE_V1", detail_kind="TRADES", rows=[row])
    except ValueError as exc:
        assert "invalid side" in str(exc)
    else:
        raise AssertionError("invalid side must fail closed")
