"""Simulation-only sizing semantics for CAND-001.

This module deliberately does not model broker lots/contracts, account balance,
risk percentage, MT5 volume constraints, or order execution. Its single purpose
is to provide a deterministic normalized quantity for simulation contracts until
a separately verified broker/economic sizing policy exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.runtime.decision import stable_fingerprint


CAND001_SIMULATION_SIZING_POLICY_VERSION = "CAND001_SIMULATION_SIZING_V1"


class QuantitySemantic(StrEnum):
    NORMALIZED_SIMULATION_UNIT = "NORMALIZED_SIMULATION_UNIT"


@dataclass(frozen=True, slots=True)
class Cand001SimulationSizingPolicy:
    """Fixed normalized simulation size with no broker/account semantics."""

    policy_version: str = CAND001_SIMULATION_SIZING_POLICY_VERSION
    quantity: float = 1.0
    quantity_semantic: QuantitySemantic = QuantitySemantic.NORMALIZED_SIMULATION_UNIT
    broker_volume_semantics: bool = False
    account_risk_semantics: bool = False

    def __post_init__(self) -> None:
        if self.policy_version != CAND001_SIMULATION_SIZING_POLICY_VERSION:
            raise ValueError(
                "policy_version must be fixed at "
                f"{CAND001_SIMULATION_SIZING_POLICY_VERSION!r}"
            )
        if isinstance(self.quantity, bool) or self.quantity != 1.0:
            raise ValueError("CAND-001 simulation quantity must be fixed at 1.0")
        if (
            not isinstance(self.quantity_semantic, QuantitySemantic)
            or self.quantity_semantic is not QuantitySemantic.NORMALIZED_SIMULATION_UNIT
        ):
            raise ValueError(
                "quantity_semantic must be NORMALIZED_SIMULATION_UNIT"
            )
        if self.broker_volume_semantics is not False:
            raise ValueError("broker volume semantics are not verified for this policy")
        if self.account_risk_semantics is not False:
            raise ValueError("account risk semantics are not defined for this policy")

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "policy_version": self.policy_version,
                "quantity": float(self.quantity),
                "quantity_semantic": self.quantity_semantic.value,
                "broker_volume_semantics": self.broker_volume_semantics,
                "account_risk_semantics": self.account_risk_semantics,
            }
        )
