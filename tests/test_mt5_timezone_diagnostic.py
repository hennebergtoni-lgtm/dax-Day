from pathlib import Path
import runpy


DIAGNOSE = runpy.run_path(
    "scripts/mt5_timezone_diagnostic.py", run_name="not_main"
)["diagnose_timezone_candidate"]


def _bundle():
    return {
        "notes": [
            "READ_ONLY",
            "RAW_TICK_CLOCK_DELTA_SECONDS=7200.000",
            "NORMALIZED_TICK_CLOCK_DELTA_SECONDS=0.250",
        ],
        "host_probe": {
            "broker_timezone": "Europe/Berlin",
            "order_execution_enabled": False,
        },
        "closed_m5_feed": {
            "broker_timezone": "Europe/Berlin",
            "timestamp_interpretation": "EXPLICIT_BROKER_WALL_CLOCK",
        },
    }


def test_consistent_candidate_is_still_not_auto_verified():
    result = DIAGNOSE(_bundle(), candidate_timezone="Europe/Berlin")
    assert result["internally_consistent"] is True
    assert result["absolute_delta_improvement_seconds"] == 7199.75
    assert result["broker_timezone_verified"] is False
    assert result["verification_state"] == "REQUIRES_EXPLICIT_HOST_CLOCK_REVIEW"
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_missing_clock_notes_block_internal_consistency():
    bundle = _bundle()
    bundle["notes"] = ["READ_ONLY"]
    result = DIAGNOSE(bundle, candidate_timezone="Europe/Berlin")
    assert "RAW_TICK_DELTA_MISSING" in result["blockers"]
    assert "NORMALIZED_TICK_DELTA_MISSING" in result["blockers"]


def test_mismatched_candidate_is_not_consistent():
    result = DIAGNOSE(_bundle(), candidate_timezone="UTC")
    assert "FEED_TIMEZONE_MISMATCH" in result["blockers"]
    assert "HOST_TIMEZONE_MISMATCH" in result["blockers"]
    assert result["broker_timezone_verified"] is False


def test_module_has_no_order_or_host_mutation():
    source = Path("scripts/mt5_timezone_diagnostic.py").read_text(encoding="utf-8").lower()
    for forbidden in ("order_send", "order_check", "mt5.initialize", "schtasks", "subprocess"):
        assert forbidden not in source
