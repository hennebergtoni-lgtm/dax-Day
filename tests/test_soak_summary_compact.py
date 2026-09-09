from datetime import datetime, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak, soak_summary


def test_soak_summary_is_compact_and_credential_free() -> None:
    bar = Mt5Bar(
        open_time=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
    )
    summary = soak_summary(run_shadow_soak((bar,)))
    assert tuple(summary) == (
        "schema_version",
        "evidence_state",
        "symbol",
        "processed",
        "blocked",
        "duplicates_suppressed",
        "run_fingerprint",
        "checkpoint_sha256",
        "execution_capability",
        "order_execution_enabled",
    )
