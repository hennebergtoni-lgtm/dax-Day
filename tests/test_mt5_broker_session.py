from datetime import datetime,time
import pytest
from daxlab.runtime.mt5_broker_session import BrokerSessionObservation,normalize_to_berlin,symbol_audit,validate_session_observation
from daxlab.runtime.mt5_readonly import BrokerSymbol

def test_dst_conversion_winter_and_summer():
    assert normalize_to_berlin(datetime.fromisoformat("2026-01-15T08:00:00+00:00"),"UTC").hour==9
    assert normalize_to_berlin(datetime.fromisoformat("2026-07-15T08:00:00+00:00"),"UTC").hour==10

def test_unknown_session_cannot_assert_hours():
    obs=BrokerSessionObservation("UTC",datetime.fromisoformat("2026-09-08T20:00:00+00:00"),time(8),time(16),"UNKNOWN")
    with pytest.raises(ValueError,match="cannot assert"): validate_session_observation(obs)

def test_observed_session_is_metadata_only():
    obs=BrokerSessionObservation("UTC",datetime.fromisoformat("2026-09-08T20:00:00+00:00"),time(8),time(16),"BROKER_OBSERVED")
    validate_session_observation(obs)

def test_configured_exact_symbol_audit():
    a=symbol_audit((BrokerSymbol("GER40",1,.1,"FULL"),),"GER40")
    assert a.state=="CONFIGURED_EXACT" and a.selected_symbol=="GER40"

def test_ambiguous_symbol_audit():
    a=symbol_audit((BrokerSymbol("GER40",1,.1,"FULL"),BrokerSymbol("DE40",1,.1,"FULL")))
    assert a.state=="AMBIGUOUS" and a.selected_symbol is None and len(a.candidates)==2

def test_disabled_alias_is_not_selected():
    a=symbol_audit((BrokerSymbol("GER40",1,.1,"DISABLED"),))
    assert a.state=="NOT_FOUND"
