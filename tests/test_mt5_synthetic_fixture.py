from datetime import datetime

from daxlab.runtime.mt5_synthetic_fixture import (
    build_synthetic_closed_m5_feed,
    synthetic_fixture_evidence_state,
)


def test_synthetic_fixture_builds_valid_closed_feed():
    feed = build_synthetic_closed_m5_feed(
        observed_at=datetime.fromisoformat("2026-09-09T06:20:00+02:00"),
        start_open_time=datetime.fromisoformat("2026-09-09T06:00:00+02:00"),
        bars=3,
    )
    assert len(feed.bars) == 3
    assert feed.requested_start_pos == 1
    assert feed.fresh
    assert not feed.discontinuities


def test_synthetic_fixture_is_explicitly_not_broker_evidence():
    assert synthetic_fixture_evidence_state() == "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
