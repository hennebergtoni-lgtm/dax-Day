from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.mt5_readonly import (
    BrokerSymbol,
    Mt5Bar,
    Mt5Health,
    closed_bar_age_seconds,
    closed_bars,
    closed_rates_start_pos,
    market_data_is_fresh,
    resolve_dax_symbol,
)


def _symbol(name: str, mode: str = "FULL") -> BrokerSymbol:
    return BrokerSymbol(name=name, digits=1, point=0.1, trade_mode=mode)


def test_configured_symbol_requires_exact_match() -> None:
    result = resolve_dax_symbol([_symbol("GER40.cash")], configured_symbol="GER40")
    assert result.state == "CONFIGURED_NOT_FOUND"
    assert result.broker_symbol is None


def test_ambiguous_aliases_fail_closed() -> None:
    result = resolve_dax_symbol([_symbol("DAX40"), _symbol("GER40")])
    assert result.state == "AMBIGUOUS"
    assert result.broker_symbol is None


def test_single_exact_tradeable_alias_resolves() -> None:
    result = resolve_dax_symbol([_symbol("GER40"), _symbol("DAX40", "DISABLED")])
    assert result.state == "AUTO_EXACT_ALIAS"
    assert result.broker_symbol is not None
    assert result.broker_symbol.name == "GER40"


def test_mt5_position_zero_is_forbidden_for_closed_bar_reads() -> None:
    with pytest.raises(ValueError, match="position >= 1"):
        closed_rates_start_pos(0)
    assert closed_rates_start_pos() == 1
    assert closed_rates_start_pos(2) == 2


def test_current_open_bar_is_excluded() -> None:
    t0 = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    bars = [
        Mt5Bar(t0, 100, 101, 99, 100.5),
        Mt5Bar(t0 + timedelta(minutes=5), 100.5, 102, 100, 101.5),
    ]
    out = closed_bars(bars, timeframe_minutes=5, observed_at=t0 + timedelta(minutes=9))
    assert len(out) == 1
    assert out[0].open_time == t0


def test_freshness_watchdog_uses_bar_close_age() -> None:
    t0 = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    observed = t0 + timedelta(minutes=6)
    assert closed_bar_age_seconds(latest_closed_bar_open=t0, timeframe_minutes=5, observed_at=observed) == 60
    assert market_data_is_fresh(latest_closed_bar_open=t0, timeframe_minutes=5, observed_at=observed, max_age_seconds=60)
    assert not market_data_is_fresh(latest_closed_bar_open=t0, timeframe_minutes=5, observed_at=observed, max_age_seconds=59)


def test_freshness_watchdog_rejects_not_yet_closed_bar() -> None:
    t0 = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="not closed"):
        closed_bar_age_seconds(latest_closed_bar_open=t0, timeframe_minutes=5, observed_at=t0 + timedelta(minutes=4))


def test_naive_observation_time_fails_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        closed_bars([], timeframe_minutes=5, observed_at=datetime(2026, 1, 2, 9, 0))


def test_health_green_requires_every_read_only_gate() -> None:
    health = Mt5Health(True, True, True, True, True, True, True)
    assert health.green
    assert not Mt5Health(True, True, True, True, True, False, True).green
