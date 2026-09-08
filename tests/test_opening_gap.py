import pytest

from daxlab.research.opening_gap import gap_closed, opening_gap


def test_up_gap_and_normalization():
    gap = opening_gap(100, 110, atr=50, prior_range=25)
    assert gap.direction == "up"
    assert gap.points == pytest.approx(10)
    assert gap.atr_fraction == pytest.approx(0.2)
    assert gap.prior_range_fraction == pytest.approx(0.4)
    assert gap_closed(gap, session_low=99, session_high=120)


def test_down_gap_closes_when_high_reaches_previous_close():
    gap = opening_gap(100, 90)
    assert gap.direction == "down"
    assert gap_closed(gap, session_low=80, session_high=101)


def test_flat_gap_is_already_closed():
    gap = opening_gap(100, 100)
    assert gap.direction == "flat"
    assert gap_closed(gap, session_low=99, session_high=101)


def test_invalid_normalizers_are_rejected():
    with pytest.raises(ValueError):
        opening_gap(100, 110, atr=0)
    with pytest.raises(ValueError):
        opening_gap(100, 110, prior_range=-1)
