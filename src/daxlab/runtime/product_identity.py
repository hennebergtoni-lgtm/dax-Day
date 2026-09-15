"""Deterministic product identity for DAX-BOT 1.x decisions and telemetry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from daxlab.runtime.decision import stable_fingerprint


IDENTITY_CONTRACT_VERSION = "DAX_BOT_PRODUCT_IDENTITY_V1"
PRODUCT_NAME = "DAX-BOT"


@dataclass(frozen=True, slots=True)
class BotProductIdentity:
    product_version: str
    candidate_id: str
    config_fingerprint: str
    product_name: str = PRODUCT_NAME
    identity_contract_version: str = IDENTITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        required = {
            "product_name": self.product_name,
            "product_version": self.product_version,
            "candidate_id": self.candidate_id,
            "config_fingerprint": self.config_fingerprint,
            "identity_contract_version": self.identity_contract_version,
        }
        for field_name, value in required.items():
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.product_name != PRODUCT_NAME:
            raise ValueError(f"product_name must be {PRODUCT_NAME!r}")
        if self.identity_contract_version != IDENTITY_CONTRACT_VERSION:
            raise ValueError(
                f"identity_contract_version must be {IDENTITY_CONTRACT_VERSION!r}"
            )

    @classmethod
    def build(
        cls,
        *,
        product_version: str,
        candidate_id: str,
        config: Any,
    ) -> BotProductIdentity:
        return cls(
            product_version=product_version,
            candidate_id=candidate_id,
            config_fingerprint=stable_fingerprint(config),
        )

    @property
    def core_version(self) -> str:
        return f"{self.product_name}/{self.product_version}/{self.candidate_id}"

    def fingerprint(self) -> str:
        return stable_fingerprint(
            {
                "candidate_id": self.candidate_id,
                "config_fingerprint": self.config_fingerprint,
                "identity_contract_version": self.identity_contract_version,
                "product_name": self.product_name,
                "product_version": self.product_version,
            }
        )
