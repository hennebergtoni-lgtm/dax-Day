"""Controlled component routing for the DAX-BOT 1.x migration.

This module selects which implementation(s) run for one component. It does not
provide safety, readiness, broker or execution authorization.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from daxlab.runtime.decision import stable_fingerprint


class TransitionMode(str, Enum):
    LEGACY = "legacy"
    DUAL_COMPARE = "dual_compare"
    BOT_1X = "bot_1x"


class ProviderSlot(str, Enum):
    LEGACY = "legacy"
    BOT_1X = "bot_1x"


@dataclass(frozen=True, slots=True)
class ComponentRoute:
    component_id: str
    contract_version: str
    mode: TransitionMode
    legacy_provider_id: str
    bot_1x_provider_id: str
    authoritative_slot: ProviderSlot
    active_config_fingerprint: str
    comparison_policy_version: str = "none"

    def __post_init__(self) -> None:
        required = {
            "component_id": self.component_id,
            "contract_version": self.contract_version,
            "legacy_provider_id": self.legacy_provider_id,
            "bot_1x_provider_id": self.bot_1x_provider_id,
            "active_config_fingerprint": self.active_config_fingerprint,
            "comparison_policy_version": self.comparison_policy_version,
        }
        for field_name, value in required.items():
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.legacy_provider_id == self.bot_1x_provider_id:
            raise ValueError("legacy and bot_1x provider ids must differ")
        if self.mode is TransitionMode.LEGACY and self.authoritative_slot is not ProviderSlot.LEGACY:
            raise ValueError("LEGACY mode requires the legacy provider to be authoritative")
        if self.mode is TransitionMode.BOT_1X and self.authoritative_slot is not ProviderSlot.BOT_1X:
            raise ValueError("BOT_1X mode requires the bot_1x provider to be authoritative")
        if self.mode is TransitionMode.DUAL_COMPARE and self.comparison_policy_version == "none":
            raise ValueError("DUAL_COMPARE requires an explicit comparison policy version")

    @property
    def comparison_enabled(self) -> bool:
        return self.mode is TransitionMode.DUAL_COMPARE

    def providers_to_run(self) -> tuple[str, ...]:
        if self.mode is TransitionMode.LEGACY:
            return (self.legacy_provider_id,)
        if self.mode is TransitionMode.BOT_1X:
            return (self.bot_1x_provider_id,)
        return (self.legacy_provider_id, self.bot_1x_provider_id)

    def authoritative_provider_id(self) -> str:
        if self.authoritative_slot is ProviderSlot.LEGACY:
            return self.legacy_provider_id
        return self.bot_1x_provider_id

    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "active_config_fingerprint": self.active_config_fingerprint,
                "authoritative_slot": self.authoritative_slot.value,
                "bot_1x_provider_id": self.bot_1x_provider_id,
                "comparison_policy_version": self.comparison_policy_version,
                "component_id": self.component_id,
                "contract_version": self.contract_version,
                "legacy_provider_id": self.legacy_provider_id,
                "mode": self.mode.value,
            }
        )


class ComponentTransitionRegistry:
    def __init__(self, routes: Iterable[ComponentRoute] = ()) -> None:
        self._routes: dict[str, ComponentRoute] = {}
        for route in routes:
            self.register(route)

    def register(self, route: ComponentRoute) -> None:
        if route.component_id in self._routes:
            raise ValueError(f"duplicate component route: {route.component_id}")
        self._routes[route.component_id] = route

    def get(self, component_id: str) -> ComponentRoute:
        return self._routes[component_id]

    def all(self) -> tuple[ComponentRoute, ...]:
        return tuple(self._routes.values())
