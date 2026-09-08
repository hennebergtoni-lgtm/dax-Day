"""Deterministic decision logging, including NO_TRADE outcomes."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class FinalAction(StrEnum):
    TRADE = "TRADE"
    NO_TRADE = "NO_TRADE"


def _json_default(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    raise TypeError(f"unsupported fingerprint value: {type(value).__name__}")


def stable_fingerprint(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def deterministic_decision_id(
    *, event_time: datetime, data_fingerprint: str, config_fingerprint: str, core_version: str
) -> str:
    return stable_fingerprint(
        {
            "event_time": event_time,
            "data_fingerprint": data_fingerprint,
            "config_fingerprint": config_fingerprint,
            "core_version": core_version,
        }
    )


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    event_time: datetime
    data_fingerprint: str
    regime: str
    structure: str
    setup: str
    filter_results: dict[str, bool]
    blockers: tuple[str, ...]
    risk_result: str
    final_action: FinalAction
    config_fingerprint: str
    decision_id: str

    @classmethod
    def build(
        cls,
        *,
        event_time: datetime,
        data_fingerprint: str,
        regime: str,
        structure: str,
        setup: str,
        filter_results: dict[str, bool],
        blockers: tuple[str, ...],
        risk_result: str,
        config: Any,
        core_version: str,
        final_action: FinalAction,
    ) -> "DecisionRecord":
        config_fingerprint = stable_fingerprint(config)
        decision_id = deterministic_decision_id(
            event_time=event_time,
            data_fingerprint=data_fingerprint,
            config_fingerprint=config_fingerprint,
            core_version=core_version,
        )
        if blockers and final_action is FinalAction.TRADE:
            raise ValueError("a blocked decision cannot be TRADE")
        return cls(
            event_time=event_time,
            data_fingerprint=data_fingerprint,
            regime=regime,
            structure=structure,
            setup=setup,
            filter_results=dict(filter_results),
            blockers=tuple(blockers),
            risk_result=risk_result,
            final_action=final_action,
            config_fingerprint=config_fingerprint,
            decision_id=decision_id,
        )
