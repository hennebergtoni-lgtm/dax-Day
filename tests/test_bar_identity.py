from datetime import datetime, timezone

import pytest

from daxlab.runtime.bar_identity import closed_bar_identity


def test_closed_bar_identity_is_deterministic() -> None:
    t = datetime(2026, 1, 2, 9, 5, tzinfo=timezone.utc)
    a = closed_bar_identity(canonical_symbol="DAX", timeframe="M5", close_time=t)
    b = closed_bar_identity(canonical_symbol="DAX", timeframe="M5", close_time=t)
    assert a == b
    assert len(a) == 64


def test_identity_changes_with_bar() -> None:
    t = datetime(2026, 1, 2, 9, 5, tzinfo=timezone.utc)
    assert closed_bar_identity(canonical_symbol="DAX", timeframe="M5", close_time=t) != closed_bar_identity(
        canonical_symbol="DAX", timeframe="M15", close_time=t
    )


def test_naive_close_time_fails_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        closed_bar_identity(
            canonical_symbol="DAX", timeframe="M5", close_time=datetime(2026, 1, 2, 9, 5)
        )
