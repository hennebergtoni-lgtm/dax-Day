"""Pure host-cycle boundary for persistent CAND-001 MT5 SHADOW operation.

The Windows supervisor remains the process/lock/probe owner. This module derives
one stable forward-stream RunManifest, restores the complete candidate checkpoint,
runs the existing MT5 SHADOW gate/runtime, and returns the next atomic checkpoint
plus deterministic publication evidence. It performs no file I/O and has no order
submission capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_mt5_shadow_runtime import (
    Cand001Mt5ShadowRuntimeResult,
    run_cand001_mt5_shadow,
)
from daxlab.runtime.candidate_shadow_checkpoint import (
    candidate_shadow_checkpoint_payload,
    parse_candidate_shadow_checkpoint_payload,
)
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_shadow_supervisor import shadow_authorization
from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle
from daxlab.runtime.operator_snapshot import OperatorSnapshot
from daxlab.runtime.paper_contracts import ExecutionIntent, PaperFillModelConfig
from daxlab.runtime.restart_reconcile import RestartReconcileResult
from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence


RUNTIME_CONTRACT_VERSION = "CAND001_MT5_SHADOW_RUNTIME_V1"
DATASET_CONTRACT_VERSION = "CAND001_MT5_CLOSED_M5_STREAM_V1"


@dataclass(frozen=True, slots=True)
class Cand001ShadowHostCycleResult:
    manifest: RunManifest
    runtime: Cand001Mt5ShadowRuntimeResult
    checkpoint_payload: dict[str, Any]
    intents_to_publish: tuple[ExecutionIntent, ...]
    outcomes_to_publish: tuple[Cand001VirtualOutcomeEvidence, ...]
    latest_operator_snapshot: OperatorSnapshot | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("candidate host cycle cannot authorize execution")
        if not self.runtime.gate.allowed:
            raise ValueError("candidate host cycle requires an allowed existing MT5 gate")
        if self.runtime.candidate_feed_result is None:
            raise ValueError("allowed candidate host cycle requires feed result")


def build_cand001_forward_manifest(
    bundle: WindowsMt5Bundle,
    *,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
) -> RunManifest:
    """Build stable identity for the open-ended validated MT5 forward stream."""
    cfg = config or Cand001Config()
    size = sizing or Cand001SimulationSizingPolicy()
    model = fill_model or PaperFillModelConfig()
    if bundle.feed is None:
        raise ValueError("candidate forward manifest requires validated CLOSED-M5 feed")
    if not bundle.host.symbols:
        raise ValueError("candidate forward manifest requires resolved broker symbol")
    broker_symbol = bundle.host.symbols[0].name
    broker_timezone = bundle.feed.broker_timezone
    timestamp_interpretation = bundle.feed.timestamp_interpretation
    if not broker_timezone or timestamp_interpretation != "EXPLICIT_BROKER_WALL_CLOCK":
        raise ValueError("candidate forward manifest requires explicit broker-time contract")

    dataset_fingerprint = stable_fingerprint(
        {
            "contract_version": DATASET_CONTRACT_VERSION,
            "broker_symbol": broker_symbol,
            "canonical_symbol": cfg.symbol,
            "timeframe": cfg.bar_timeframe,
            "broker_timezone": broker_timezone,
            "timestamp_interpretation": timestamp_interpretation,
        }
    )
    engine_fingerprint = stable_fingerprint(
        {
            "runtime_contract_version": RUNTIME_CONTRACT_VERSION,
            "core_version": cfg.product_identity().core_version,
            "ruleset_version": cfg.ruleset_version,
            "fill_model_fingerprint": model.fingerprint,
        }
    )
    return RunManifest.build(
        dataset_fingerprint=dataset_fingerprint,
        engine_fingerprint=engine_fingerprint,
        config={"candidate": cfg, "sizing": size},
        mode=RuntimeMode.SHADOW,
    )


def run_cand001_shadow_host_cycle(
    bundle: WindowsMt5Bundle,
    *,
    single_instance_lock_held: bool,
    checkpoint_payload: Mapping[str, Any] | None = None,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
    restart_reconcile: RestartReconcileResult | None = None,
) -> Cand001ShadowHostCycleResult:
    """Restore, run and prepare one complete atomic CAND-001 SHADOW checkpoint."""
    cfg = config or Cand001Config()
    size = sizing or Cand001SimulationSizingPolicy()
    model = fill_model or PaperFillModelConfig()
    manifest = build_cand001_forward_manifest(
        bundle,
        config=cfg,
        sizing=size,
        fill_model=model,
    )
    state = (
        parse_candidate_shadow_checkpoint_payload(
            checkpoint_payload,
            run_manifest=manifest,
            config=cfg,
        )
        if checkpoint_payload is not None
        else Cand001ShadowState()
    )

    runtime = run_cand001_mt5_shadow(
        state,
        bundle,
        authorization=shadow_authorization(),
        single_instance_lock_held=single_instance_lock_held,
        run_manifest=manifest,
        config=cfg,
        sizing=size,
        fill_model=model,
        restart_reconcile=restart_reconcile,
    )
    if not runtime.gate.allowed or runtime.candidate_feed_result is None:
        raise RuntimeError(
            "candidate host cycle called while existing MT5 SHADOW gate is blocked"
        )

    steps = runtime.candidate_feed_result.steps
    intents = tuple(
        step.intent_to_publish for step in steps if step.intent_to_publish is not None
    )
    outcomes = tuple(
        step.outcome_to_publish for step in steps if step.outcome_to_publish is not None
    )
    latest = steps[-1].operator_snapshot if steps else None
    checkpoint = candidate_shadow_checkpoint_payload(
        runtime.state,
        run_manifest=manifest,
        config=cfg,
    )
    return Cand001ShadowHostCycleResult(
        manifest=manifest,
        runtime=runtime,
        checkpoint_payload=checkpoint,
        intents_to_publish=intents,
        outcomes_to_publish=outcomes,
        latest_operator_snapshot=latest,
    )
