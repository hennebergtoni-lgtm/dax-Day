from datetime import datetime, timedelta, timezone

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import run_shadow_soak


def test_checkpoint_hash_changes_as_unique_processed_state_advances() -> None:
    start = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    first_bar = Mt5Bar(start, 100.0, 101.0, 99.0, 100.5)
    second_bar = Mt5Bar(start + timedelta(minutes=5), 100.5, 101.5, 99.5, 101.0)
    first = run_shadow_soak((first_bar,))
    second = run_shadow_soak((second_bar,), checkpoint=first.checkpoint)
    assert first.checkpoint.payload_sha256 != second.checkpoint.payload_sha256
