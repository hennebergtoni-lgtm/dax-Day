from dataclasses import fields

import pytest

from daxlab.runtime.product_identity import (
    IDENTITY_CONTRACT_VERSION,
    PRODUCT_NAME,
    BotProductIdentity,
)


def test_product_identity_is_deterministic_for_equivalent_config():
    left = BotProductIdentity.build(
        product_version="1.0-alpha",
        candidate_id="CAND-001",
        config={"rr": 1.5, "or_minutes": 15},
    )
    right = BotProductIdentity.build(
        product_version="1.0-alpha",
        candidate_id="CAND-001",
        config={"or_minutes": 15, "rr": 1.5},
    )
    assert left.config_fingerprint == right.config_fingerprint
    assert left.fingerprint() == right.fingerprint()
    assert left.core_version == "DAX-BOT/1.0-alpha/CAND-001"


def test_product_identity_changes_when_config_candidate_or_version_changes():
    base = BotProductIdentity.build(
        product_version="1.0-alpha",
        candidate_id="CAND-001",
        config={"rr": 1.5},
    )
    config_changed = BotProductIdentity.build(
        product_version="1.0-alpha",
        candidate_id="CAND-001",
        config={"rr": 2.0},
    )
    candidate_changed = BotProductIdentity.build(
        product_version="1.0-alpha",
        candidate_id="CAND-002",
        config={"rr": 1.5},
    )
    version_changed = BotProductIdentity.build(
        product_version="1.1-alpha",
        candidate_id="CAND-001",
        config={"rr": 1.5},
    )
    assert base.fingerprint() != config_changed.fingerprint()
    assert base.fingerprint() != candidate_changed.fingerprint()
    assert base.fingerprint() != version_changed.fingerprint()


def test_product_identity_rejects_empty_or_wrong_contract_identity():
    with pytest.raises(ValueError, match="product_version"):
        BotProductIdentity(
            product_version="",
            candidate_id="CAND-001",
            config_fingerprint="cfg",
        )
    with pytest.raises(ValueError, match="product_name"):
        BotProductIdentity(
            product_version="1.0-alpha",
            candidate_id="CAND-001",
            config_fingerprint="cfg",
            product_name="OTHER",
        )
    with pytest.raises(ValueError, match="identity_contract_version"):
        BotProductIdentity(
            product_version="1.0-alpha",
            candidate_id="CAND-001",
            config_fingerprint="cfg",
            identity_contract_version="OTHER",
        )


def test_identity_contract_constants_are_explicit():
    assert PRODUCT_NAME == "DAX-BOT"
    assert IDENTITY_CONTRACT_VERSION == "DAX_BOT_PRODUCT_IDENTITY_V1"


def test_product_identity_contains_no_execution_or_broker_authorization_fields():
    field_names = {field.name for field in fields(BotProductIdentity)}
    forbidden_tokens = ("execution", "order", "broker", "credential", "live_authorized")
    assert not any(token in name for token in forbidden_tokens for name in field_names)
