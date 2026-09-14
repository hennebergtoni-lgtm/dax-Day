from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from daxlab.research.atr_regime import causal_hysteresis_regime


START = datetime(2026, 9, 14, 8, tzinfo=timezone.utc)


def feature(values, **changes):
    observations = [{"available_at": START + timedelta(minutes=index), "value": value}
                    for index, value in enumerate(values)]
    kwargs = dict(decision_at=START + timedelta(minutes=100), enter_threshold=25,
                  exit_threshold=20, confirmation_observations=2, source_sha256="a" * 64)
    return causal_hysteresis_regime(observations, **{**kwargs, **changes})


def test_dead_band_and_consecutive_confirmation_prevent_flapping():
    result = feature([26, 26, 24, 21, 19, 21, 19, 19])
    assert [row["active"] for row in result["trace"]] == [False, True, True, True, True, True, True, False]
    assert result["flip_count"] == 2
    assert result["hypothesis_validation"] == "NOT_TESTED_AGAINST_COSTED_OOS_LEDGER"
    assert result["execution_capability"] == "NONE"


def test_future_and_equal_time_values_cannot_change_causal_prefix():
    time = START + timedelta(minutes=3)
    assert feature([26, 26, 24], decision_at=time) == feature(
        [26, 26, 24, float("nan"), None, 1000], decision_at=time,
    )


def test_absent_feature_never_invents_neutral_regime():
    result = feature([30], decision_at=START)
    assert result["active"] is None
    assert result["status"] == "INSUFFICIENT_SAMPLE"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, None, -1, 10**1000])
def test_invalid_available_feature_rejects(value):
    with pytest.raises(ValueError):
        feature([value])


@pytest.mark.parametrize("changes", [
    {"enter_threshold": float("nan")}, {"exit_threshold": True},
    {"enter_threshold": 20, "exit_threshold": 25}, {"exit_threshold": -1},
    {"confirmation_observations": True}, {"confirmation_observations": 0},
    {"source_sha256": "missing"}, {"decision_at": START.replace(tzinfo=None)},
])
def test_invalid_predeclared_spec_rejects(changes):
    with pytest.raises(ValueError):
        feature([26], **changes)


def test_duplicate_or_out_of_order_availability_rejects():
    rows = [{"available_at": START, "value": 26},
            {"available_at": START + timedelta(minutes=1), "value": 26}]
    for sequence in ([rows[0], rows[0]], list(reversed(rows))):
        with pytest.raises(ValueError):
            causal_hysteresis_regime(
                sequence, decision_at=START + timedelta(minutes=10),
                enter_threshold=25, exit_threshold=20,
                confirmation_observations=2, source_sha256="a" * 64,
            )


def test_trial_parameters_are_bound_to_diagnostic_identity():
    assert feature([26, 26])["identity_sha256"] != feature(
        [26, 26], confirmation_observations=1,
    )["identity_sha256"]
