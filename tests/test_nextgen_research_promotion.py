from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.contracts import ExperimentManifest, REFERENCE_COSTS, REFERENCE_WF, ResearchStatus
from daxlab.research.promotion import (
    EvaluationContractV1,
    PromotionState,
    ResearchExperimentV1,
    ResearchPromotionArtifactV1,
    canonical_promotion_json,
)


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


SOURCE_COMMIT = "1" * 40


def build_experiment(*, fill: str = "CONSERVATIVE_OHLC") -> ResearchExperimentV1:
    manifest = ExperimentManifest(
        experiment_id="NEXTGEN-CAND001-WF-V1",
        hypothesis="Candidate behavior is evaluated without changing strategy rules.",
        status=ResearchStatus.WF_OOS,
        baseline="CAND-001",
        parameters={"or_minutes": 15, "entry": "confirmed_breakout"},
        data_fingerprint=h("dataset"),
        engine_fingerprint=h("engine"),
    )
    evaluation = EvaluationContractV1.build(
        split_id="WF_45_20_20",
        walk_forward=REFERENCE_WF,
        cost_models=REFERENCE_COSTS,
        fill_assumption=fill,
    )
    return ResearchExperimentV1.build(
        manifest=manifest,
        strategy_id="CAND-001",
        strategy_version="1",
        strategy_fingerprint=h("strategy"),
        config_fingerprint=h("config"),
        dataset_manifest_fingerprint=h("dataset-manifest"),
        evaluation=evaluation,
        robustness_evidence_refs=(
            "evidence/oos_summary.json#sha256=" + h("oos"),
            "evidence/stability.json#sha256=" + h("stability"),
        ),
        source_commit=SOURCE_COMMIT,
        limitations=(
            "Historical evidence is descriptive and is not a profitability proof.",
            "Real-host SHADOW verification is a separate gate.",
        ),
    )


def test_promotion_is_deterministic_and_binds_required_provenance() -> None:
    experiment = build_experiment()
    first = ResearchPromotionArtifactV1.build(
        experiment=experiment,
        promotion_state=PromotionState.REVIEW_READY,
    )
    second = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(),
        promotion_state=PromotionState.REVIEW_READY,
    )

    assert first == second
    assert first.experiment_fingerprint == experiment.experiment_fingerprint
    assert first.dataset_fingerprint == experiment.manifest.data_fingerprint
    assert first.dataset_manifest_fingerprint == experiment.dataset_manifest_fingerprint
    assert first.evaluation_fingerprint == experiment.evaluation.fingerprint
    assert first.product_strategy.source_experiment_fingerprint == experiment.experiment_fingerprint
    assert first.product_strategy.source_commit == SOURCE_COMMIT
    assert len(first.product_strategy.artifact_fingerprint) == 64
    assert len(first.promotion_fingerprint) == 64
    assert first.execution_capability == "NONE"
    assert first.order_execution_authorized is False
    assert first.paper_authorized is False
    assert first.live_authorized is False


def test_evaluation_or_promotion_state_changes_only_the_expected_identity_layer() -> None:
    base = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(), promotion_state=PromotionState.REVIEW_READY
    )
    changed_fill = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(fill="NEXT_BAR_OPEN"),
        promotion_state=PromotionState.REVIEW_READY,
    )
    accepted = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(),
        promotion_state=PromotionState.PRODUCT_STRATEGY_ACCEPTED,
    )

    assert base.evaluation_fingerprint != changed_fill.evaluation_fingerprint
    assert base.experiment_fingerprint != changed_fill.experiment_fingerprint
    assert base.product_strategy.artifact_fingerprint != changed_fill.product_strategy.artifact_fingerprint
    assert base.promotion_fingerprint != changed_fill.promotion_fingerprint
    assert base.product_strategy == accepted.product_strategy
    assert base.promotion_fingerprint != accepted.promotion_fingerprint


def test_promotion_cannot_enable_external_execution_or_hide_tampering() -> None:
    artifact = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(), promotion_state=PromotionState.PRODUCT_STRATEGY_ACCEPTED
    )

    with pytest.raises(ValueError, match="no execution capability"):
        replace(artifact, execution_capability="BROKER")
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(artifact, order_execution_authorized=True)
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(artifact, paper_authorized=True)
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(artifact, live_authorized=True)
    with pytest.raises(ValueError, match="product strategy artifact fingerprint mismatch"):
        replace(artifact.product_strategy, artifact_fingerprint=h("tampered"))
    with pytest.raises(ValueError, match="promotion fingerprint mismatch"):
        replace(artifact, limitations=("Tampered limitation.",))


def test_experiment_fails_closed_on_missing_evidence_or_noncanonical_parameters() -> None:
    experiment = build_experiment()
    with pytest.raises(ValueError, match="robustness_evidence_refs"):
        ResearchExperimentV1.build(
            manifest=experiment.manifest,
            strategy_id=experiment.strategy_id,
            strategy_version=experiment.strategy_version,
            strategy_fingerprint=experiment.strategy_fingerprint,
            config_fingerprint=experiment.config_fingerprint,
            dataset_manifest_fingerprint=experiment.dataset_manifest_fingerprint,
            evaluation=experiment.evaluation,
            robustness_evidence_refs=(),
            source_commit=experiment.source_commit,
            limitations=experiment.limitations,
        )

    bad_manifest = ExperimentManifest(
        experiment_id="BAD",
        hypothesis="noncanonical parameters are rejected",
        status=ResearchStatus.RESEARCH,
        baseline="NONE",
        parameters={"not_json": {1, 2}},
        data_fingerprint=h("dataset"),
        engine_fingerprint=h("engine"),
    )
    with pytest.raises(ValueError, match="canonical JSON"):
        ResearchExperimentV1.build(
            manifest=bad_manifest,
            strategy_id="TEST",
            strategy_version="1",
            strategy_fingerprint=h("strategy"),
            config_fingerprint=h("config"),
            dataset_manifest_fingerprint=h("dataset-manifest"),
            evaluation=experiment.evaluation,
            robustness_evidence_refs=("evidence/test.json#sha256=" + h("evidence"),),
            source_commit=SOURCE_COMMIT,
            limitations=("Research only.",),
        )


def test_canonical_json_round_trip_is_stable_and_explicit_about_safety() -> None:
    artifact = ResearchPromotionArtifactV1.build(
        experiment=build_experiment(), promotion_state=PromotionState.REVIEW_READY
    )
    text = canonical_promotion_json(artifact)
    payload = json.loads(text)

    assert text == json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_authorized"] is False
    assert payload["paper_authorized"] is False
    assert payload["live_authorized"] is False


def test_promotion_contract_has_no_runtime_broker_candidate_or_mt5_dependency() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/research/promotion.py"
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
