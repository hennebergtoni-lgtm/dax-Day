from datetime import UTC, datetime, timedelta

import pytest

from daxlab.runtime.time import assert_strict_utc_order, to_berlin


def test_spring_dst_jump_is_deterministic_in_berlin():
    before = datetime(2026, 3, 29, 0, 55, tzinfo=UTC)
    after = before + timedelta(minutes=5)
    assert to_berlin(before).isoformat() == "2026-03-29T01:55:00+01:00"
    assert to_berlin(after).isoformat() == "2026-03-29T03:00:00+02:00"
    assert_strict_utc_order(before, after)


def test_autumn_dst_fold_preserves_absolute_order():
    first = datetime(2026, 10, 25, 0, 30, tzinfo=UTC)
    second = first + timedelta(hours=1)
    first_berlin = to_berlin(first)
    second_berlin = to_berlin(second)
    assert first_berlin.hour == second_berlin.hour == 2
    assert first_berlin.utcoffset() != second_berlin.utcoffset()
    assert_strict_utc_order(first, second)


def test_naive_runtime_timestamp_is_rejected():
    naive = datetime(2026, 3, 29, 1, 0, tzinfo=UTC).replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone-aware"):
        to_berlin(naive)
