from datetime import date

from scripts.benchmark_cand001_pipeline import (
    BARS_PER_SESSION,
    SCHEMA_VERSION,
    benchmark,
    synthetic_session,
)


def test_synthetic_benchmark_session_has_full_103_bar_feed_surface():
    bars = synthetic_session(date(2026, 1, 5), base_price=25000.0)

    assert len(bars) == BARS_PER_SESSION == 103
    assert bars[0].event_time.strftime("%H:%M") == "09:00"
    assert bars[-1].event_time.strftime("%H:%M") == "17:30"


def test_benchmark_reports_metrics_without_imposing_performance_threshold():
    result = benchmark(sessions=1, repeats=1)

    assert result["schema_version"] == SCHEMA_VERSION
    assert result["candidate_id"] == "CAND-001"
    assert result["core_version"] == "DAX-BOT/1.0-alpha/CAND-001"
    assert result["events_per_repeat"] == 103
    assert result["median_ns_per_event"] > 0
    assert result["p95_ns_per_event"] > 0
    assert result["median_events_per_second"] > 0
    assert result["performance_gate"] == "OBSERVATION_ONLY"
    assert len(result["terminal_snapshot_fingerprint"]) == 64
