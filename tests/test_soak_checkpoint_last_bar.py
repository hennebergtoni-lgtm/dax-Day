from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import bar_fingerprint, run_shadow_soak


def test_checkpoint_tracks_last_accepted_closed_bar_fingerprint() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    first = Mt5Bar(start, 100.0, 101.0, 99.0, 100.5)
    last = Mt5Bar(start + timedelta(minutes=5), 100.5, 101.5, 99.5, 101.0)
    result = run_shadow_soak((first, last))
    assert result.checkpoint.last_bar_fingerprint == bar_fingerprint(last)
