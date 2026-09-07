from daxlab.core.execution import Bar, Bracket, ExitReason, Side, resolve_bracket_bar


def test_long_ambiguous_bar_resolves_stop_first() -> None:
    bar = Bar(open=100, high=112, low=88, close=105)
    assert resolve_bracket_bar(bar, Bracket(stop=90, target=110), Side.LONG) is ExitReason.STOP


def test_short_ambiguous_bar_resolves_stop_first() -> None:
    bar = Bar(open=100, high=112, low=88, close=95)
    assert resolve_bracket_bar(bar, Bracket(stop=110, target=90), Side.SHORT) is ExitReason.STOP


def test_target_only_is_target() -> None:
    bar = Bar(open=100, high=111, low=96, close=108)
    assert resolve_bracket_bar(bar, Bracket(stop=90, target=110), Side.LONG) is ExitReason.TARGET
