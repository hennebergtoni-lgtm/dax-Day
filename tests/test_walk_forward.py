from daxlab.contracts import REFERENCE_WF
from daxlab.research.walk_forward import build_walk_forwards


def test_reference_window_lengths_and_step() -> None:
    days = list(range(100))
    windows = build_walk_forwards(days, REFERENCE_WF)
    assert len(windows) == 2
    assert len(windows[0].train) == 45
    assert len(windows[0].oos) == 20
    assert windows[0].train[-1] == 44
    assert windows[0].oos[0] == 45
    assert windows[1].train[0] == 20


def test_train_and_oos_do_not_overlap_within_window() -> None:
    windows = build_walk_forwards(list(range(200)), REFERENCE_WF)
    for window in windows:
        assert set(window.train).isdisjoint(window.oos)
