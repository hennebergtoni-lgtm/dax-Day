from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak, soak_recovery_payload, soak_summary


def test_soak_evidence_contains_no_credential_or_account_fields() -> None:
    at = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    result = run_shadow_soak(
        (
            Mt5Bar(
                open_time=at - timedelta(minutes=5),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
            ),
        )
    )
    text = repr(soak_summary(result)).lower() + repr(soak_recovery_payload(result)).lower()
    for forbidden in ("password", "login", "account_id", "email", "phone", "token", "secret"):
        assert forbidden not in text
