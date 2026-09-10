from pathlib import Path
import runpy


EVALUATE = runpy.run_path(
    "scripts/mt5_broker_timezone_evidence.py", run_name="not_main"
)["evaluate_broker_timezone_evidence"]


def _probe():
    return {
        "order_execution_enabled": False,
        "broker_timezone": "Europe/Berlin",
        "timestamp_interpretation": "EXPLICIT_BROKER_WALL_CLOCK",
        "observed_at_utc": "2026-09-10T03:30:00+00:00",
        "host_clock_compared": True,
    }


def test_consistent_explicit_host_evidence_can_verify():
    result = EVALUATE(_probe(), candidate_timezone="Europe/Berlin")
    assert result["status"] == "VERIFIED"
    assert result["broker_timezone_verified"] is True
    assert result["blockers"] == []
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_no_host_clock_comparison_stays_unverified():
    probe = _probe()
    probe["host_clock_compared"] = False
    result = EVALUATE(probe, candidate_timezone="Europe/Berlin")
    assert result["status"] == "UNVERIFIED"
    assert "HOST_CLOCK_COMPARISON_REQUIRED" in result["blockers"]


def test_timezone_mismatch_stays_unverified():
    result = EVALUATE(_probe(), candidate_timezone="UTC")
    assert result["broker_timezone_verified"] is False
    assert "PROBE_TIMEZONE_MISMATCH" in result["blockers"]


def test_invalid_timezone_and_timestamp_stay_unverified():
    probe = _probe()
    probe["observed_at_utc"] = "not-a-time"
    result = EVALUATE(probe, candidate_timezone="Not/AZone")
    assert "CANDIDATE_TIMEZONE_INVALID" in result["blockers"]
    assert "OBSERVED_AT_UTC_INVALID" in result["blockers"]


def test_module_has_no_mt5_or_host_mutation():
    source = Path("scripts/mt5_broker_timezone_evidence.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "order_send",
        "order_check",
        "mt5.initialize",
        "schtasks",
        "subprocess",
    ):
        assert forbidden not in source
