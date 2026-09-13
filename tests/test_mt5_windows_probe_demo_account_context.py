from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mt5_windows_probe.py"
_SPEC = importlib.util.spec_from_file_location("daxlab_mt5_windows_probe_test", _SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("unable to load mt5_windows_probe.py for test")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
collect_probe = _MODULE.collect_probe

LOGIN = 25115284


def _fake_mt5(*, account_mode: int = 0, include_mode_constants: bool = True):
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    symbol = SimpleNamespace(
        name="DE40",
        digits=2,
        point=0.01,
        trade_mode=4,
        trade_contract_size=1.0,
        volume_min=0.01,
        volume_step=0.01,
        volume_max=100.0,
        volume_limit=0.0,
        trade_tick_size=0.01,
        trade_tick_value=0.01,
        trade_tick_value_profit=0.01,
        trade_tick_value_loss=0.01,
        currency_profit="EUR",
        currency_margin="EUR",
        margin_initial=0.0,
        margin_maintenance=0.0,
    )
    account = SimpleNamespace(
        login=LOGIN,
        server="Broker-Demo",
        trade_mode=account_mode,
        trade_allowed=True,
    )
    fake = SimpleNamespace(
        SYMBOL_TRADE_MODE_DISABLED=0,
        SYMBOL_TRADE_MODE_LONGONLY=1,
        SYMBOL_TRADE_MODE_SHORTONLY=2,
        SYMBOL_TRADE_MODE_CLOSEONLY=3,
        SYMBOL_TRADE_MODE_FULL=4,
        TIMEFRAME_M5=5,
        initialize=lambda: True,
        last_error=lambda: (0, "OK"),
        terminal_info=lambda: SimpleNamespace(connected=True),
        account_info=lambda: account,
        symbols_get=lambda: (symbol,),
        symbol_select=lambda name, selected: True,
        symbol_info_tick=lambda name: SimpleNamespace(time=now_epoch),
        copy_rates_from_pos=lambda name, timeframe, start_pos, bars: (
            {
                "time": now_epoch - 600,
                "open": 23000.0,
                "high": 23010.0,
                "low": 22990.0,
                "close": 23005.0,
            },
            {
                "time": now_epoch - 300,
                "open": 23005.0,
                "high": 23015.0,
                "low": 23000.0,
                "close": 23010.0,
            },
        ),
        shutdown=lambda: None,
    )
    if include_mode_constants:
        fake.ACCOUNT_TRADE_MODE_DEMO = 0
        fake.ACCOUNT_TRADE_MODE_CONTEST = 1
        fake.ACCOUNT_TRADE_MODE_REAL = 2
    return fake


def _collect(monkeypatch, fake_mt5):
    monkeypatch.setitem(__import__("sys").modules, "MetaTrader5", fake_mt5)
    return collect_probe(
        configured_symbol="DE40",
        bars=2,
        max_age_seconds=600.0,
    )


def test_existing_probe_emits_redacted_demo_context_without_order_api(monkeypatch):
    fake_mt5 = _fake_mt5(account_mode=0)
    assert not hasattr(fake_mt5, "order_send")

    bundle = _collect(monkeypatch, fake_mt5)
    context = bundle["host_probe"]["demo_account_context"]
    encoded = json.dumps(bundle, sort_keys=True)

    assert context["account_mode"] == "DEMO"
    assert context["server"] == "Broker-Demo"
    assert context["symbol"] == "DE40"
    assert context["trade_allowed"] is True
    assert len(context["account_fingerprint"]) == 64
    assert str(LOGIN) not in encoded
    assert '"login"' not in encoded
    assert '"account_id"' not in encoded
    assert context["execution_capability"] == "NONE"
    assert context["order_execution_enabled"] is False
    assert "DEMO_ACCOUNT_CONTEXT_STATE=AVAILABLE_REDACTED" in bundle["notes"]


def test_real_account_is_observed_as_real_not_demo(monkeypatch):
    bundle = _collect(monkeypatch, _fake_mt5(account_mode=2))
    context = bundle["host_probe"]["demo_account_context"]
    assert context["account_mode"] == "REAL"
    assert context["trade_allowed"] is True


def test_missing_runtime_mode_constants_fail_closed_to_unknown(monkeypatch):
    bundle = _collect(
        monkeypatch,
        _fake_mt5(account_mode=0, include_mode_constants=False),
    )
    context = bundle["host_probe"]["demo_account_context"]
    assert context["account_mode"] == "UNKNOWN"


def test_invalid_account_identity_omits_demo_context_but_keeps_shadow_probe(monkeypatch):
    fake_mt5 = _fake_mt5(account_mode=0)
    fake_mt5.account_info = lambda: SimpleNamespace(
        login=None,
        server="Broker-Demo",
        trade_mode=0,
        trade_allowed=True,
    )

    bundle = _collect(monkeypatch, fake_mt5)
    assert bundle["host_probe"]["account_connected"] is True
    assert "demo_account_context" not in bundle["host_probe"]
    assert "DEMO_ACCOUNT_CONTEXT_STATE=UNAVAILABLE_FAIL_CLOSED" in bundle["notes"]
    assert bundle["host_probe"]["order_execution_enabled"] is False
