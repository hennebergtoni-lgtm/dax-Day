from __future__ import annotations

import pytest

from daxlab.runtime.mt5_feed_payload import feed_blocker, parse_closed_m5_feed


def payload() -> dict:
    return {
        "observed_at": "2026-09-08T10:16:00+02:00",
        "requested_start_pos": 1,
        "max_age_seconds": 360,
        "bars": [
            {
                "open_time": "2026-09-08T10:05:00+02:00",
                "open": 100,
                "high": 103,
                "low": 99,
                "close": 102,
            },
            {
                "open_time": "2026-09-08T10:10:00+02:00",
                "open": 102,
                "high": 104,
                "low": 101,
                "close": 103,
            },
        ],
    }


def test_valid_closed_feed() -> None:
    feed = parse_closed_m5_feed(payload())
    assert feed.fresh
    assert not feed.discontinuities
    assert len(feed.latest_closed_fingerprint) == 64
    assert feed.broker_timezone is None
    assert feed.timestamp_interpretation is None
    assert feed_blocker(feed) is None


def test_explicit_broker_timestamp_contract_is_preserved() -> None:
    item = payload()
    item["broker_timezone"] = "Europe/Berlin"
    item["timestamp_interpretation"] = "EXPLICIT_BROKER_WALL_CLOCK"
    feed = parse_closed_m5_feed(item)
    assert feed.broker_timezone == "Europe/Berlin"
    assert feed.timestamp_interpretation == "EXPLICIT_BROKER_WALL_CLOCK"


def test_raw_utc_timestamp_contract_is_valid_without_timezone() -> None:
    item = payload()
    item["broker_timezone"] = None
    item["timestamp_interpretation"] = "RAW_UTC_ASSUMPTION"
    feed = parse_closed_m5_feed(item)
    assert feed.broker_timezone is None
    assert feed.timestamp_interpretation == "RAW_UTC_ASSUMPTION"


def test_rejects_partial_broker_timestamp_contract() -> None:
    item = payload()
    item["broker_timezone"] = "Europe/Berlin"
    with pytest.raises(ValueError, match="supplied together"):
        parse_closed_m5_feed(item)


def test_rejects_explicit_interpretation_without_timezone() -> None:
    item = payload()
    item["broker_timezone"] = None
    item["timestamp_interpretation"] = "EXPLICIT_BROKER_WALL_CLOCK"
    with pytest.raises(ValueError, match="raw UTC interpretation required"):
        parse_closed_m5_feed(item)


def test_rejects_raw_interpretation_with_timezone() -> None:
    item = payload()
    item["broker_timezone"] = "Europe/Berlin"
    item["timestamp_interpretation"] = "RAW_UTC_ASSUMPTION"
    with pytest.raises(ValueError, match="explicit broker wall-clock"):
        parse_closed_m5_feed(item)


def test_rejects_unknown_timestamp_interpretation() -> None:
    item = payload()
    item["broker_timezone"] = "Europe/Berlin"
    item["timestamp_interpretation"] = "GUESS"
    with pytest.raises(ValueError, match="unsupported timestamp_interpretation"):
        parse_closed_m5_feed(item)


def test_rejects_bar_zero_request() -> None:
    item = payload()
    item["requested_start_pos"] = 0
    with pytest.raises(ValueError, match="position >= 1"):
        parse_closed_m5_feed(item)


def test_rejects_naive_bar_time() -> None:
    item = payload()
    item["bars"][0]["open_time"] = "2026-09-08T10:05:00"
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_closed_m5_feed(item)


def test_rejects_bad_ohlc() -> None:
    item = payload()
    item["bars"][0]["high"] = 98
    with pytest.raises(ValueError, match="OHLC invariant"):
        parse_closed_m5_feed(item)


def test_rejects_duplicate_or_unsorted_times() -> None:
    item = payload()
    item["bars"][1]["open_time"] = item["bars"][0]["open_time"]
    with pytest.raises(ValueError, match="unique"):
        parse_closed_m5_feed(item)


def test_rejects_open_bar() -> None:
    item = payload()
    item["bars"][-1]["open_time"] = "2026-09-08T10:15:00+02:00"
    with pytest.raises(ValueError, match="unclosed"):
        parse_closed_m5_feed(item)


def test_stale_reason() -> None:
    item = payload()
    item["observed_at"] = "2026-09-08T10:30:00+02:00"
    assert feed_blocker(parse_closed_m5_feed(item)) == "MARKET_DATA_STALE"


def test_gap_is_diagnostic_not_filled() -> None:
    item = payload()
    item["bars"][1]["open_time"] = "2026-09-08T10:15:00+02:00"
    item["observed_at"] = "2026-09-08T10:21:00+02:00"
    feed = parse_closed_m5_feed(item)
    assert len(feed.bars) == 2
    assert feed.discontinuities
    assert feed_blocker(feed) == "MARKET_DATA_DISCONTINUITY"
