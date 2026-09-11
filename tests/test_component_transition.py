from dataclasses import fields

import pytest

from daxlab.runtime.component_transition import (
    ComponentRoute,
    ComponentTransitionRegistry,
    ProviderSlot,
    TransitionMode,
)


def _route(
    *,
    component_id: str = "structure",
    mode: TransitionMode = TransitionMode.LEGACY,
    authoritative_slot: ProviderSlot = ProviderSlot.LEGACY,
    comparison_policy_version: str = "none",
) -> ComponentRoute:
    return ComponentRoute(
        component_id=component_id,
        contract_version="v1",
        mode=mode,
        legacy_provider_id="legacy.structure.v1",
        bot_1x_provider_id="bot1x.structure.v1",
        authoritative_slot=authoritative_slot,
        active_config_fingerprint="cfg-sha256",
        comparison_policy_version=comparison_policy_version,
    )


def test_legacy_mode_runs_only_legacy_and_keeps_it_authoritative():
    route = _route()
    assert route.providers_to_run() == ("legacy.structure.v1",)
    assert route.authoritative_provider_id() == "legacy.structure.v1"
    assert route.comparison_enabled is False


def test_bot_1x_mode_runs_only_bot_1x_and_requires_it_authoritative():
    route = _route(
        mode=TransitionMode.BOT_1X,
        authoritative_slot=ProviderSlot.BOT_1X,
    )
    assert route.providers_to_run() == ("bot1x.structure.v1",)
    assert route.authoritative_provider_id() == "bot1x.structure.v1"
    assert route.comparison_enabled is False


def test_dual_compare_runs_both_but_has_exactly_one_authoritative_provider():
    route = _route(
        mode=TransitionMode.DUAL_COMPARE,
        authoritative_slot=ProviderSlot.LEGACY,
        comparison_policy_version="decision-parity-v1",
    )
    assert route.providers_to_run() == (
        "legacy.structure.v1",
        "bot1x.structure.v1",
    )
    assert route.authoritative_provider_id() == "legacy.structure.v1"
    assert route.comparison_enabled is True


def test_legacy_and_bot_modes_reject_wrong_authoritative_slot():
    with pytest.raises(ValueError, match="LEGACY mode"):
        _route(authoritative_slot=ProviderSlot.BOT_1X)
    with pytest.raises(ValueError, match="BOT_1X mode"):
        _route(mode=TransitionMode.BOT_1X, authoritative_slot=ProviderSlot.LEGACY)


def test_dual_compare_requires_versioned_comparison_policy():
    with pytest.raises(ValueError, match="comparison policy"):
        _route(mode=TransitionMode.DUAL_COMPARE)


def test_same_provider_cannot_fill_both_transition_slots():
    with pytest.raises(ValueError, match="provider ids must differ"):
        ComponentRoute(
            component_id="entry",
            contract_version="v1",
            mode=TransitionMode.LEGACY,
            legacy_provider_id="same",
            bot_1x_provider_id="same",
            authoritative_slot=ProviderSlot.LEGACY,
            active_config_fingerprint="cfg",
        )


def test_registry_rejects_duplicate_component_ids():
    route = _route()
    with pytest.raises(ValueError, match="duplicate component route"):
        ComponentTransitionRegistry([route, route])


def test_route_fingerprint_is_deterministic_and_mode_sensitive():
    first = _route()
    second = _route()
    changed = _route(
        mode=TransitionMode.BOT_1X,
        authoritative_slot=ProviderSlot.BOT_1X,
    )
    assert first.fingerprint() == second.fingerprint()
    assert first.fingerprint() != changed.fingerprint()


def test_transition_contract_contains_no_execution_or_broker_authorization_fields():
    field_names = {field.name for field in fields(ComponentRoute)}
    forbidden_tokens = ("execution", "order", "broker", "credential", "live_authorized")
    assert not any(token in name for token in forbidden_tokens for name in field_names)
