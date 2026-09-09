from datetime import datetime, timezone

from daxlab.runtime.mt5_broker_session import normalize_to_berlin


def test_berlin_winter_offset() -> None:
    value = datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)
    berlin = normalize_to_berlin(value, "UTC")
    assert berlin.hour == 9
    assert berlin.utcoffset().total_seconds() == 3600


def test_berlin_summer_offset() -> None:
    value = datetime(2026, 7, 15, 8, 0, tzinfo=timezone.utc)
    berlin = normalize_to_berlin(value, "UTC")
    assert berlin.hour == 10
    assert berlin.utcoffset().total_seconds() == 7200


def test_berlin_dst_transition_is_not_hard_coded() -> None:
    before = normalize_to_berlin(datetime(2026, 3, 29, 0, 30, tzinfo=timezone.utc), "UTC")
    after = normalize_to_berlin(datetime(2026, 3, 29, 1, 30, tzinfo=timezone.utc), "UTC")
    assert before.utcoffset().total_seconds() == 3600
    assert after.utcoffset().total_seconds() == 7200
