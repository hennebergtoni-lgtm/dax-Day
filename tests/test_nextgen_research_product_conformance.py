from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.contracts import ExperimentManifest, REFERENCE_COSTS, REFERENCE_WF, ResearchStatus
from daxlab.domain.market import Candle, InstrumentId
from daxlab.domain.strategy import StrategyDecision, TradeDirection, TradePlan
from daxlab.engine.replay import ENGINE_VERSION, replay_candles
from daxlab.research.conformance import (
    ConformanceMismatch,
    ResearchExpectedDecisionsV1,
    canonical_conformance_json,
    canonical_research_decisions_json,
    verify_research_product_conformance,
)
from daxlab.research.promotion import (
    EvaluationContractV1,
    PromotionState,
    ResearchExperimentV1,
    ResearchPromotionArtifactV1,
)
from daxlab.strategies.contracts import StrategyTransition


INSTRUMENT = InstrumentId("DAX.CFD")
STRATEGY_ID = "SYNTHETIC-CONFORMANCE"
STRATEGY_VERSION = "1"
STRATEGY_FINGERPRINT = "05b69c4c2733372ef32665c651e37f1994d499563ac2fc98c0a57afa90185318"
CONFIG_FINGERPRINT = sha256(b"conformance-config").hexdigest()
DATASET_FINGERPRINT = sha256(b"canonical-dataset").hexdigest()
DATASET_MANIFEST_FINGERPRINT = sha256(b"canonical-dataset-manifest").hexdigest()
FROZEN_REPLAY_INPUT_FINGERPRINT = (
    "2711cd1a1fd2cf69580295b3057fe5119a3732c04d1cc698ce073b4ffdb0d4a7"
)
FROZEN_DECISION_IDS = (
    "9c5d3646194d78a6a7098f20b736b07c7c40d81ccb4442d792c3d6404de7e1f5",
    "2ce96edf5d94196704f08bf94772564b6d5f504035eeadbd16618d6a9bf11ce5",
    "5bb2e6398e8326a282946b00b426b93ed201c41df5c32c98df94c138c16a1ec9",
)
FROZEN_DECISION_IDS_FINGERPRINT = (
    "d9760ce4f320fe515064f771a98fbfda2ccf6780ce22ecb8bf0cf964b9c42762"
)
SOURCE_COMMIT = "1" * 40


class SyntheticConformanceStrategy:
    strategy_id = STRATEGY_ID
    strategy_version = STRATEGY_VERSION
    strategy_fingerprint = STRATEGY_FINGERPRINT

    def initial_state(self) -> int:
        return 0

    def on_candle(self, state: int, candle: Candle) -> StrategyTransition[int]:
        if candle.close > 101:
            decision = StrategyDecision.trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("ABOVE_THRESHOLD",),
                trade_plan=TradePlan(
                    instrument_id=candle.instrument_id,
                    direction=TradeDirection.LONG,
                    entry_price=candle.close,
                    stop_price=candle.close - 1,
                    target_price=candle.close + 2,
                ),
            )
        else:
            decision = StrategyDecision.no_trade(
                strategy_id=self.strategy_id,
                strategy_version=self.strategy_version,
                strategy_fingerprint=self.strategy_fingerprint,
                event_time=candle.close_time,
                instrument_id=candle.instrument_id,
                reason_codes=("BELOW_THRESHOLD",),
            )
        return StrategyTransition(state=state + 1, decision=decision)


class ReasonDriftStrategy(SyntheticConformanceStrategy):
    def on_candle(self, state: int, candle: Candle) -> StrategyTransition[int]:
        transition = super().on_candle(state, candle)
        if candle.close <= 101:
            return transition
        decision = StrategyDecision.trade(
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            strategy_fingerprint=self.strategy_fingerprint,
            event_time=candle.close_time,
            instrument_id=candle.instrument_id,
            reason_codes=("DRIFTED_REASON",),
            trade_plan=transition.decision.trade_plan,
        )
        return StrategyTransition(state=transition.state, decision=decision)


def frozen_candles() -> tuple[Candle, ...]:
    candles: list[Candle] = []
    for minute, close in ((0, 100.0), (5, 101.0), (10, 102.0)):
        event = datetime(2026, 9, 10, 8, minute, tzinfo=timezone.utc)
        close_time = event + timedelta(minutes=5)
        candles.append(
            Candle(
                instrument_id=INSTRUMENT,
                timeframe="M5",
                event_time=event,
                close_time=close_time,
                open=close - 0.5,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=None,
                source="SYNTHETIC_CONFORMANCE_V1",
                received_at=close_time + timedelta(seconds=1),
                is_closed=True,
            )
        )
    return tuple(candles)


def build_promotion() -> ResearchPromotionArtifactV1:
    manifest = ExperimentManifest(
        experiment_id="NEXTGEN-CONFORMANCE-V1",
        hypothesis="Frozen research decisions must match canonical product replay exactly.",
        status=ResearchStatus.WF_OOS,
        baseline="SYNTHETIC-CONFORMANCE-V1",
        parameters={"fixture": "SYNTHETIC-CONFORMANCE-V1"},
        data_fingerprint=DATASET_FINGERPRINT,
        engine_fingerprint=sha256(ENGINE_VERSION.encode("utf-8")).hexdigest(),
    )
    evaluation = EvaluationContractV1.build(
        split_id="WF_45_20_20",
        walk_forward=REFERENCE_WF,
        cost_models=REFERENCE_COSTS,
        fill_assumption="CONSERVATIVE_OHLC",
    )
    experiment = ResearchExperimentV1.build(
        manifest=manifest,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        strategy_fingerprint=STRATEGY_FINGERPRINT,
        config_fingerprint=CONFIG_FINGERPRINT,
        dataset_manifest_fingerprint=DATASET_MANIFEST_FINGERPRINT,
        evaluation=evaluation,
        robustness_evidence_refs=(
            "tests/fixtures/conformance/robustness.json#sha256="
            + sha256(b"robustness").hexdigest(),
        ),
        source_commit=SOURCE_COMMIT,
        limitations=("Synthetic fixture proves conformance mechanics only.",),
    )
    return ResearchPromotionArtifactV1.build(
        experiment=experiment,
        promotion_state=PromotionState.REVIEW_READY,
    )


def build_research_expected(
    promotion: ResearchPromotionArtifactV1,
    **overrides: object,
) -> ResearchExpectedDecisionsV1:
    values: dict[str, object] = {
        "fixture_id": "SYNTHETIC-CONFORMANCE-V1",
        "source_experiment_fingerprint": promotion.experiment_fingerprint,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_fingerprint": STRATEGY_FINGERPRINT,
        "config_fingerprint": CONFIG_FINGERPRINT,
        "dataset_fingerprint": DATASET_FINGERPRINT,
        "dataset_manifest_fingerprint": DATASET_MANIFEST_FINGERPRINT,
        "replay_input_fingerprint": FROZEN_REPLAY_INPUT_FINGERPRINT,
        "expected_decision_ids": FROZEN_DECISION_IDS,
        "source_reference": "tests/test_nextgen_research_product_conformance.py",
    }
    values.update(overrides)
    return ResearchExpectedDecisionsV1.build(**values)  # type: ignore[arg-type]


def test_frozen_fixture_literals_match_canonical_product_replay() -> None:
    replay = replay_candles(SyntheticConformanceStrategy(), frozen_candles())

    assert replay.manifest.input_fingerprint == FROZEN_REPLAY_INPUT_FINGERPRINT
    assert tuple(item.decision_id for item in replay.decisions) == FROZEN_DECISION_IDS
    assert replay.decision_ids_fingerprint == FROZEN_DECISION_IDS_FINGERPRINT
    assert replay.execution_capability == "NONE"
    assert replay.order_execution_enabled is False


def test_matching_research_fixture_produces_deterministic_conformance_artifact() -> None:
    promotion = build_promotion()
    research = build_research_expected(promotion)
    replay = replay_candles(SyntheticConformanceStrategy(), frozen_candles())

    first = verify_research_product_conformance(
        promotion=promotion,
        research=research,
        replay=replay,
    )
    second = verify_research_product_conformance(
        promotion=promotion,
        research=research,
        replay=replay,
    )

    assert first == second
    assert first.status == "MATCH"
    assert first.research_artifact_fingerprint == research.artifact_fingerprint
    assert first.promotion_fingerprint == promotion.promotion_fingerprint
    assert first.replay_result_fingerprint == replay.result_fingerprint
    assert first.decision_ids_fingerprint == FROZEN_DECISION_IDS_FINGERPRINT
    assert first.execution_capability == "NONE"
    assert first.order_execution_authorized is False
    assert first.paper_authorized is False
    assert first.live_authorized is False


def test_conformance_fails_closed_on_research_provenance_drift() -> None:
    promotion = build_promotion()
    replay = replay_candles(SyntheticConformanceStrategy(), frozen_candles())

    cases = (
        ("source experiment fingerprint", {"source_experiment_fingerprint": sha256(b"x").hexdigest()}),
        ("strategy fingerprint", {"strategy_fingerprint": sha256(b"x").hexdigest()}),
        ("config fingerprint", {"config_fingerprint": sha256(b"x").hexdigest()}),
        ("dataset fingerprint", {"dataset_fingerprint": sha256(b"x").hexdigest()}),
        (
            "dataset manifest fingerprint",
            {"dataset_manifest_fingerprint": sha256(b"x").hexdigest()},
        ),
    )
    for expected_message, overrides in cases:
        research = build_research_expected(promotion, **overrides)
        with pytest.raises(ConformanceMismatch, match=expected_message):
            verify_research_product_conformance(
                promotion=promotion,
                research=research,
                replay=replay,
            )


def test_conformance_detects_input_drift_even_when_decisions_stay_identical() -> None:
    promotion = build_promotion()
    research = build_research_expected(promotion)
    candles = list(frozen_candles())
    candles[-1] = replace(
        candles[-1],
        received_at=candles[-1].received_at + timedelta(seconds=1),
    )
    replay = replay_candles(SyntheticConformanceStrategy(), tuple(candles))

    assert tuple(item.decision_id for item in replay.decisions) == FROZEN_DECISION_IDS
    assert replay.manifest.input_fingerprint != FROZEN_REPLAY_INPUT_FINGERPRINT
    with pytest.raises(ConformanceMismatch, match="replay input fingerprint"):
        verify_research_product_conformance(
            promotion=promotion,
            research=research,
            replay=replay,
        )


def test_conformance_detects_decision_semantic_drift_with_same_strategy_identity() -> None:
    promotion = build_promotion()
    research = build_research_expected(promotion)
    replay = replay_candles(ReasonDriftStrategy(), frozen_candles())

    assert replay.manifest.strategy_fingerprint == STRATEGY_FINGERPRINT
    assert replay.manifest.input_fingerprint == FROZEN_REPLAY_INPUT_FINGERPRINT
    assert replay.decision_ids_fingerprint != FROZEN_DECISION_IDS_FINGERPRINT
    with pytest.raises(ConformanceMismatch, match="ordered product decision ids"):
        verify_research_product_conformance(
            promotion=promotion,
            research=research,
            replay=replay,
        )


def test_artifacts_are_tamper_checked_and_canonical_json_is_stable() -> None:
    promotion = build_promotion()
    research = build_research_expected(promotion)
    replay = replay_candles(SyntheticConformanceStrategy(), frozen_candles())
    conformance = verify_research_product_conformance(
        promotion=promotion,
        research=research,
        replay=replay,
    )

    with pytest.raises(ValueError, match="artifact fingerprint mismatch"):
        replace(research, source_reference="tampered")
    with pytest.raises(ValueError, match="conformance fingerprint mismatch"):
        replace(conformance, replay_result_fingerprint=sha256(b"tampered").hexdigest())
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(conformance, live_authorized=True)

    research_json = canonical_research_decisions_json(research)
    conformance_json = canonical_conformance_json(conformance)
    assert research_json == json.dumps(
        json.loads(research_json), sort_keys=True, indent=2, ensure_ascii=True
    ) + "\n"
    assert conformance_json == json.dumps(
        json.loads(conformance_json), sort_keys=True, indent=2, ensure_ascii=True
    ) + "\n"


def test_conformance_module_has_no_runtime_broker_candidate_or_mt5_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/research/conformance.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = (
        "MetaTrader5",
        "daxlab.runtime",
        "daxlab.strategies.cand001",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden
    )
