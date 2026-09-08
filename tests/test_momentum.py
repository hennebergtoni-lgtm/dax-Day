from datetime import datetime, timedelta, timezone

from daxlab.research.momentum import MomentumBar, completed_momentum_state


def _bar(minute: int, open_: float, close: float) -> MomentumBar:
    time = datetime(2026, 1, 2, 9, minute, tzinfo=timezone.utc)
    return MomentumBar(
        time=time,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
    )


def test_same_entry_time_bar_is_excluded() -> None:
    bars = [_bar(5, 100, 101), _bar(10, 101, 102), _bar(15, 102, 103)]
    state = completed_momentum_state(bars, entry_time=bars[-1].time)
    assert state is not None
    assert state.state_time == bars[-2].time


def test_future_pollution_does_not_change_prior_state() -> None:
    bars = [
        _bar(5, 100, 101),
        _bar(10, 101, 102),
        _bar(15, 102, 103),
        _bar(20, 103, 104),
    ]
    entry = bars[-1].time + timedelta(minutes=1)
    before = completed_momentum_state(bars, entry_time=entry)
    polluted = bars + [
        MomentumBar(
            time=entry + timedelta(minutes=5),
            open=1000,
            high=2000,
            low=1,
            close=2,
        )
    ]
    after = completed_momentum_state(polluted, entry_time=entry)
    assert before == after


def test_fixed_horizon_and_directional_close_features() -> None:
    bars = [
        _bar(5, 100, 101),
        _bar(10, 101, 102),
        _bar(15, 102, 103),
        _bar(20, 103, 104),
    ]
    state = completed_momentum_state(bars, entry_time=bars[-1].time + timedelta(seconds=1))
    assert state is not None
    assert state.return_1 == 104 / 103 - 1
    assert state.return_3 == 104 / 101 - 1
    assert state.directional_closes_3 == 3
    assert 0.0 <= state.body_fraction <= 1.0
