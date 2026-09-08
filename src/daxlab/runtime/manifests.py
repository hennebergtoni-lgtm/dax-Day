"""Deterministic manifests for replay, shadow, paper and live execution surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint


@dataclass(frozen=True, slots=True)
class RunManifest:
    dataset_fingerprint: str
    engine_fingerprint: str
    config_fingerprint: str
    mode: RuntimeMode
    manifest_fingerprint: str

    @classmethod
    def build(
        cls,
        *,
        dataset_fingerprint: str,
        engine_fingerprint: str,
        config: Any,
        mode: RuntimeMode,
    ) -> "RunManifest":
        config_fingerprint = stable_fingerprint(config)
        payload = {
            "dataset_fingerprint": dataset_fingerprint,
            "engine_fingerprint": engine_fingerprint,
            "config_fingerprint": config_fingerprint,
            "mode": mode.value,
        }
        return cls(
            dataset_fingerprint=dataset_fingerprint,
            engine_fingerprint=engine_fingerprint,
            config_fingerprint=config_fingerprint,
            mode=mode,
            manifest_fingerprint=stable_fingerprint(payload),
        )


@dataclass(frozen=True, slots=True)
class DecisionLogManifest:
    decisions: int
    trades: int
    no_trades: int
    decision_ids_fingerprint: str

    @classmethod
    def build(cls, records: tuple[DecisionRecord, ...]) -> "DecisionLogManifest":
        trades = sum(record.final_action is FinalAction.TRADE for record in records)
        no_trades = sum(record.final_action is FinalAction.NO_TRADE for record in records)
        return cls(
            decisions=len(records),
            trades=trades,
            no_trades=no_trades,
            decision_ids_fingerprint=stable_fingerprint(
                tuple(record.decision_id for record in records)
            ),
        )


def assert_run_manifest_matches(expected: RunManifest, observed: RunManifest) -> None:
    """Abort before replay/execution if any run identity component drifts."""
    if expected.dataset_fingerprint != observed.dataset_fingerprint:
        raise RuntimeError("run manifest dataset fingerprint drift")
    if expected.engine_fingerprint != observed.engine_fingerprint:
        raise RuntimeError("run manifest engine fingerprint drift")
    if expected.config_fingerprint != observed.config_fingerprint:
        raise RuntimeError("run manifest config fingerprint drift")
    if expected.mode is not observed.mode:
        raise RuntimeError("run manifest mode drift")
    if expected.manifest_fingerprint != observed.manifest_fingerprint:
        raise RuntimeError("run manifest fingerprint drift")
