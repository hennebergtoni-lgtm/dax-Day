from dataclasses import FrozenInstanceError, fields

import pytest

from daxlab.runtime.candidate_config import (
    BREAKOUT_SEMANTIC_PROVENANCE,
    CANDIDATE_ID,
    PRODUCT_VERSION,
    RULESET_VERSION,
    SELECTION_PROVENANCE,
    Cand001Config,
    DirectionPolicy,
    EntryRule,
    RegimePolicy,
    StopRule,
    StructureRule,
    TargetRule,
)
from daxlab.runtime.decision import stable_fingerprint


def test_cand001_defaults_are_the_frozen_alpha_rule_snapshot():
    config = Cand001Config()

    assert config.candidate_id == "CAND-001"
    assert config.ruleset_version == "CAND_001_RULESET_V1"
    assert config.symbol == "DE40"
    assert config.bar_timeframe == "5m"
    assert config.session_timezone == "Europe/Berlin"
    assert config.session_start == "09:00"
    assert config.session_end == "17:30"
    assert config.or_minutes == 15
    assert config.regime_policy is RegimePolicy.OBSERVE_ONLY
    assert config.structure_rule is StructureRule.OPENING_RANGE
    assert config.entry_rule is EntryRule.CONFIRMED_BREAKOUT_CLOSE
    assert config.direction_policy is DirectionPolicy.BOTH
    assert config.stop_rule is StopRule.OR_OPPOSITE
    assert config.target_rule is TargetRule.FIXED_R_MULTIPLE
    assert config.reward_risk == 1.5
    assert config.max_trades_per_session == 1


def test_cand001_product_identity_reuses_canonical_config_fingerprint():
    config = Cand001Config()
    identity = config.product_identity()

    assert PRODUCT_VERSION == "1.0-alpha"
    assert CANDIDATE_ID == "CAND-001"
    assert identity.core_version == "DAX-BOT/1.0-alpha/CAND-001"
    assert identity.config_fingerprint == stable_fingerprint(config)
    assert identity.candidate_id == config.candidate_id


def test_cand001_config_is_immutable():
    config = Cand001Config()
    with pytest.raises(FrozenInstanceError):
        config.or_minutes = 5


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("candidate_id", "CAND-999"),
        ("ruleset_version", "OTHER"),
        ("symbol", "GER40"),
        ("bar_timeframe", "1m"),
        ("session_timezone", "UTC"),
        ("session_start", "08:00"),
        ("session_end", "18:00"),
        ("or_minutes", 5),
        ("reward_risk", 2.0),
        ("max_trades_per_session", 2),
    ],
)
def test_cand001_rejects_mutated_fixed_strategy_values(field_name, value):
    with pytest.raises(ValueError, match=field_name):
        Cand001Config(**{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("regime_policy", "OBSERVE_ONLY"),
        ("structure_rule", "OPENING_RANGE"),
        ("entry_rule", "CONFIRMED_BREAKOUT_CLOSE"),
        ("direction_policy", "BOTH"),
        ("stop_rule", "OR_OPPOSITE"),
        ("target_rule", "FIXED_R_MULTIPLE"),
    ],
)
def test_cand001_requires_typed_rule_enums(field_name, value):
    with pytest.raises(ValueError, match=field_name):
        Cand001Config(**{field_name: value})


def test_cand001_semantic_provenance_is_explicit():
    assert BREAKOUT_SEMANTIC_PROVENANCE == "REUSE_ELIGIBLE_RESEARCH_SEMANTIC"
    assert SELECTION_PROVENANCE == "NEW_1X_SELECTION"
    assert RULESET_VERSION == "CAND_001_RULESET_V1"


def test_cand001_contract_contains_no_broker_or_execution_authorization_fields():
    field_names = {field.name for field in fields(Cand001Config)}
    forbidden_tokens = (
        "broker",
        "credential",
        "execution_capability",
        "order_execution",
        "live_authorized",
    )
    assert not any(token in name for token in forbidden_tokens for name in field_names)
