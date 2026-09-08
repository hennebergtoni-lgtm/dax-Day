from __future__ import annotations
import pytest
from daxlab.runtime.mt5_feed_payload import feed_blocker, parse_closed_m5_feed

def payload():
    return {"observed_at":"2026-09-08T10:16:00+02:00","requested_start_pos":1,"max_age_seconds":360,"bars":[
        {"open_time":"2026-09-08T10:05:00+02:00","open":100,"high":103,"low":99,"close":102},
        {"open_time":"2026-09-08T10:10:00+02:00","open":102,"high":104,"low":101,"close":103}]}

def test_valid_closed_feed():
    feed=parse_closed_m5_feed(payload()); assert feed.fresh; assert not feed.discontinuities; assert len(feed.latest_closed_fingerprint)==64; assert feed_blocker(feed) is None

def test_rejects_bar_zero_request():
    p=payload(); p["requested_start_pos"]=0
    with pytest.raises(ValueError,match="position >= 1"): parse_closed_m5_feed(p)

def test_rejects_naive_bar_time():
    p=payload(); p["bars"][0]["open_time"]="2026-09-08T10:05:00"
    with pytest.raises(ValueError,match="timezone-aware"): parse_closed_m5_feed(p)

def test_rejects_bad_ohlc():
    p=payload(); p["bars"][0]["high"]=98
    with pytest.raises(ValueError,match="OHLC invariant"): parse_closed_m5_feed(p)

def test_rejects_duplicate_or_unsorted_times():
    p=payload(); p["bars"][1]["open_time"]=p["bars"][0]["open_time"]
    with pytest.raises(ValueError,match="unique"): parse_closed_m5_feed(p)

def test_rejects_open_bar():
    p=payload(); p["bars"][-1]["open_time"]="2026-09-08T10:15:00+02:00"
    with pytest.raises(ValueError,match="unclosed"): parse_closed_m5_feed(p)

def test_stale_reason():
    p=payload(); p["observed_at"]="2026-09-08T10:30:00+02:00"
    assert feed_blocker(parse_closed_m5_feed(p))=="MARKET_DATA_STALE"

def test_gap_is_diagnostic_not_filled():
    p=payload(); p["bars"][1]["open_time"]="2026-09-08T10:15:00+02:00"; p["observed_at"]="2026-09-08T10:21:00+02:00"
    feed=parse_closed_m5_feed(p); assert len(feed.bars)==2; assert feed.discontinuities; assert feed_blocker(feed)=="MARKET_DATA_DISCONTINUITY"
