from daxlab.research.filter_recommender import RegimeSnapshot, suggest_filters
from daxlab.research.filter_registry import default_research_registry


def test_research_suggestions_remain_observe_only():
    snapshot = RegimeSnapshot(
        volatility="normal",
        structure="breakout_retest",
        prior_day="extended",
        session_phase="open",
    )
    out = suggest_filters(snapshot, default_research_registry())
    assert {x.key for x in out} == {"bb001", "prev_range_atr"}
    assert {x.action for x in out} == {"observe"}


def test_irrelevant_regime_does_not_force_suggestions():
    snapshot = RegimeSnapshot(
        volatility="normal",
        structure="range",
        prior_day="normal",
        session_phase="midday",
    )
    assert suggest_filters(snapshot, default_research_registry()) == ()
