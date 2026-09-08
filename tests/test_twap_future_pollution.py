from datetime import datetime, timezone

from daxlab.research.twap import TwapBar, session_twap_before_entry


def test_future_suffix_cannot_change_prior_twap_state() -> None:
    entry = datetime(2026, 1, 15, 8, 20, tzinfo=timezone.utc)
    prefix = [
        TwapBar(datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc), 100.0),
        TwapBar(datetime(2026, 1, 15, 8, 5, tzinfo=timezone.utc), 102.0),
        TwapBar(datetime(2026, 1, 15, 8, 10, tzinfo=timezone.utc), 104.0),
    ]
    baseline = session_twap_before_entry(prefix, entry_time=entry)
    polluted = session_twap_before_entry(
        prefix
        + [
            TwapBar(datetime(2026, 1, 15, 8, 15, tzinfo=timezone.utc), -99999.0),
            TwapBar(datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc), 99999.0),
        ],
        entry_time=entry,
    )
    assert baseline == polluted
