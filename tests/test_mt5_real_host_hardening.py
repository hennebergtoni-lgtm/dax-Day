from datetime import datetime, timezone

from daxlab.runtime.mt5_broker_session import server_wall_clock_epoch_to_utc
from daxlab.runtime.mt5_readonly import BrokerSymbol, resolve_dax_symbol


def _symbol(name: str, trade_mode: str) -> BrokerSymbol:
    return BrokerSymbol(
        name=name,
        digits=2,
        point=0.01,
        trade_mode=trade_mode,
        contract_size=1.0,
        volume_min=0.1,
        volume_step=0.1,
    )


def test_auto_resolution_ignores_bare_dax_etf_and_selects_de40_data_only() -> None:
    symbols = (
        _symbol("DE40", "DISABLED"),
        _symbol("DAX", "FULL"),
    )

    resolution = resolve_dax_symbol(symbols, allow_data_only=True)

    assert resolution.state == "AUTO_EXACT_ALIAS_DATA_ONLY"
    assert resolution.broker_symbol is not None
    assert resolution.broker_symbol.name == "DE40"
    assert resolution.candidates == ("DE40",)


def test_bare_dax_remains_available_only_when_explicitly_configured() -> None:
    symbols = (
        _symbol("DE40", "DISABLED"),
        _symbol("DAX", "FULL"),
    )

    resolution = resolve_dax_symbol(symbols, configured_symbol="DAX", allow_data_only=True)

    assert resolution.state == "CONFIGURED_EXACT"
    assert resolution.broker_symbol is not None
    assert resolution.broker_symbol.name == "DAX"


def test_eet_server_wall_clock_normalizes_summer_time_without_fixed_offset() -> None:
    encoded = datetime(2026, 9, 9, 20, 28, 15, tzinfo=timezone.utc).timestamp()

    normalized = server_wall_clock_epoch_to_utc(encoded, "EET")

    assert normalized == datetime(2026, 9, 9, 17, 28, 15, tzinfo=timezone.utc)


def test_eet_server_wall_clock_normalizes_winter_time_without_fixed_offset() -> None:
    encoded = datetime(2026, 1, 9, 20, 28, 15, tzinfo=timezone.utc).timestamp()

    normalized = server_wall_clock_epoch_to_utc(encoded, "EET")

    assert normalized == datetime(2026, 1, 9, 18, 28, 15, tzinfo=timezone.utc)
