from datetime import datetime, timezone

from daxlab.runtime.mt5_host_contract import Mt5HostObservation, validate_read_only_host
from daxlab.runtime.mt5_readonly import BrokerSymbol


def _obs(**overrides):
    values = dict(
        observed_at=datetime(2026, 9, 8, 16, 30, tzinfo=timezone.utc),
        terminal_connected=True,
        account_connected=True,
        account_trade_allowed=True,
        order_execution_enabled=False,
        engine_loop_healthy=True,
        clock_ok=True,
        symbols=(BrokerSymbol("GER40", 1, 0.1, "FULL"),),
    )
    values.update(overrides)
    return Mt5HostObservation(**values)


def test_healthy_read_only_handshake_can_be_green() -> None:
    result = validate_read_only_host(_obs(), market_data_fresh=True)
    assert result.reason == "READ_ONLY_HEALTHY"
    assert result.health.green


def test_execution_flag_fails_closed_even_on_demo_account() -> None:
    result = validate_read_only_host(_obs(order_execution_enabled=True), market_data_fresh=True)
    assert result.reason == "ORDER_EXECUTION_ENABLED"
    assert not result.health.green
    assert not result.health.read_only_mode


def test_ambiguous_dax_symbols_block_health() -> None:
    symbols = (
        BrokerSymbol("GER40", 1, 0.1, "FULL"),
        BrokerSymbol("DAX40", 1, 0.1, "FULL"),
    )
    result = validate_read_only_host(_obs(symbols=symbols), market_data_fresh=True)
    assert result.reason == "SYMBOL_AMBIGUOUS"
    assert not result.health.green


def test_stale_market_data_blocks_health() -> None:
    result = validate_read_only_host(_obs(), market_data_fresh=False)
    assert result.reason == "MARKET_DATA_STALE"
    assert not result.health.green
