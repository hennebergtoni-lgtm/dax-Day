"""Deterministic Research -> Product promotion metadata for DAX-BOT NextGen."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from daxlab.contracts import CostModel, ExperimentManifest, WalkForwardSpec

EXPERIMENT_SCHEMA = "DAXLAB_RESEARCH_EXPERIMENT_V1"
PROMOTION_SCHEMA = "DAXLAB_RESEARCH_PROMOTION_V1"
PRODUCT_ARTIFACT_SCHEMA = "DAXLAB_PRODUCT_STRATEGY_ARTIFACT_V1"


class PromotionState(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    REVIEW_READY = "REVIEW_READY"
    PRODUCT_STRATEGY_ACCEPTED = "PRODUCT_STRATEGY_ACCEPTED"


@dataclass(frozen=True, slots=True)
class EvaluationContractV1:
    split_id: str
    walk_forward: WalkForwardSpec
    cost_models: tuple[CostModel, ...]
    fill_assumption: str
    fingerprint: str

    @classmethod
    def build(cls, *, split_id: str, walk_forward: WalkForwardSpec,
              cost_models: tuple[CostModel, ...], fill_assumption: str) -> "EvaluationContractV1":
        payload = _evaluation_payload(split_id, walk_forward, cost_models, fill_assumption)
        return cls(split_id, walk_forward, cost_models, fill_assumption, _fp(payload))

    def __post_init__(self) -> None:
        _token(self.split_id, "split_id")
        _token(self.fill_assumption, "fill_assumption")
        if not self.cost_models:
            raise ValueError("cost_models must not be empty")
        names = tuple(item.name for item in self.cost_models)
        if len(set(names)) != len(names):
            raise ValueError("cost model names must be unique")
        _sha(self.fingerprint, "evaluation fingerprint")
        if self.fingerprint != _fp(_evaluation_payload(
            self.split_id, self.walk_forward, self.cost_models, self.fill_assumption
        )):
            raise ValueError("evaluation fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class ResearchExperimentV1:
    manifest: ExperimentManifest
    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    config_fingerprint: str
    dataset_manifest_fingerprint: str
    evaluation: EvaluationContractV1
    robustness_evidence_refs: tuple[str, ...]
    source_commit: str
    limitations: tuple[str, ...]
    experiment_fingerprint: str
    schema_version: str = EXPERIMENT_SCHEMA

    @classmethod
    def build(cls, *, manifest: ExperimentManifest, strategy_id: str, strategy_version: str,
              strategy_fingerprint: str, config_fingerprint: str,
              dataset_manifest_fingerprint: str, evaluation: EvaluationContractV1,
              robustness_evidence_refs: tuple[str, ...], source_commit: str,
              limitations: tuple[str, ...]) -> "ResearchExperimentV1":
        payload = _experiment_payload(
            manifest, strategy_id, strategy_version, strategy_fingerprint,
            config_fingerprint, dataset_manifest_fingerprint, evaluation,
            robustness_evidence_refs, source_commit, limitations,
        )
        return cls(
            manifest, strategy_id, strategy_version, strategy_fingerprint,
            config_fingerprint, dataset_manifest_fingerprint, evaluation,
            robustness_evidence_refs, source_commit, limitations, _fp(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != EXPERIMENT_SCHEMA:
            raise ValueError("unsupported experiment schema")
        _token(self.strategy_id, "strategy_id")
        _token(self.strategy_version, "strategy_version")
        for name, value in (
            ("strategy_fingerprint", self.strategy_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("data_fingerprint", self.manifest.data_fingerprint),
            ("engine_fingerprint", self.manifest.engine_fingerprint),
            ("dataset_manifest_fingerprint", self.dataset_manifest_fingerprint),
            ("experiment_fingerprint", self.experiment_fingerprint),
        ):
            _sha(value, name)
        _commit(self.source_commit)
        _nonempty_tuple(self.robustness_evidence_refs, "robustness_evidence_refs")
        _nonempty_tuple(self.limitations, "limitations")
        if len(set(self.robustness_evidence_refs)) != len(self.robustness_evidence_refs):
            raise ValueError("robustness evidence references must be unique")
        if self.experiment_fingerprint != _fp(_experiment_payload(
            self.manifest, self.strategy_id, self.strategy_version,
            self.strategy_fingerprint, self.config_fingerprint,
            self.dataset_manifest_fingerprint, self.evaluation,
            self.robustness_evidence_refs, self.source_commit, self.limitations,
        )):
            raise ValueError("experiment fingerprint mismatch")

    @property
    def dataset_fingerprint(self) -> str:
        return self.manifest.data_fingerprint


@dataclass(frozen=True, slots=True)
class ProductStrategyArtifactV1:
    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    config_fingerprint: str
    source_experiment_fingerprint: str
    source_commit: str
    artifact_fingerprint: str
    schema_version: str = PRODUCT_ARTIFACT_SCHEMA

    @classmethod
    def from_experiment(cls, experiment: ResearchExperimentV1) -> "ProductStrategyArtifactV1":
        payload = _product_payload(experiment)
        return cls(
            experiment.strategy_id, experiment.strategy_version,
            experiment.strategy_fingerprint, experiment.config_fingerprint,
            experiment.experiment_fingerprint, experiment.source_commit, _fp(payload),
        )

    def __post_init__(self) -> None:
        if self.schema_version != PRODUCT_ARTIFACT_SCHEMA:
            raise ValueError("unsupported product artifact schema")
        _sha(self.artifact_fingerprint, "artifact_fingerprint")
        _commit(self.source_commit)


@dataclass(frozen=True, slots=True)
class ResearchPromotionArtifactV1:
    promotion_state: PromotionState
    experiment_fingerprint: str
    dataset_fingerprint: str
    dataset_manifest_fingerprint: str
    evaluation_fingerprint: str
    robustness_evidence_refs: tuple[str, ...]
    product_strategy: ProductStrategyArtifactV1
    source_commit: str
    limitations: tuple[str, ...]
    promotion_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_authorized: bool = False
    paper_authorized: bool = False
    live_authorized: bool = False
    schema_version: str = PROMOTION_SCHEMA

    @classmethod
    def build(cls, *, experiment: ResearchExperimentV1,
              promotion_state: PromotionState) -> "ResearchPromotionArtifactV1":
        product = ProductStrategyArtifactV1.from_experiment(experiment)
        values = dict(
            promotion_state=promotion_state,
            experiment_fingerprint=experiment.experiment_fingerprint,
            dataset_fingerprint=experiment.dataset_fingerprint,
            dataset_manifest_fingerprint=experiment.dataset_manifest_fingerprint,
            evaluation_fingerprint=experiment.evaluation.fingerprint,
            robustness_evidence_refs=experiment.robustness_evidence_refs,
            product_strategy=product,
            source_commit=experiment.source_commit,
            limitations=experiment.limitations,
        )
        return cls(**values, promotion_fingerprint=_fp(_promotion_payload(**values)))

    def __post_init__(self) -> None:
        if self.schema_version != PROMOTION_SCHEMA:
            raise ValueError("unsupported promotion schema")
        if self.execution_capability != "NONE":
            raise ValueError("promotion artifact has no execution capability")
        if self.order_execution_authorized or self.paper_authorized or self.live_authorized:
            raise ValueError("promotion artifact cannot authorize external execution")
        for name, value in (
            ("experiment_fingerprint", self.experiment_fingerprint),
            ("dataset_fingerprint", self.dataset_fingerprint),
            ("dataset_manifest_fingerprint", self.dataset_manifest_fingerprint),
            ("evaluation_fingerprint", self.evaluation_fingerprint),
            ("promotion_fingerprint", self.promotion_fingerprint),
        ):
            _sha(value, name)
        _commit(self.source_commit)
        if self.product_strategy.source_experiment_fingerprint != self.experiment_fingerprint:
            raise ValueError("product strategy experiment mismatch")
        if self.product_strategy.source_commit != self.source_commit:
            raise ValueError("product strategy source commit mismatch")
        if self.promotion_fingerprint != _fp(_promotion_payload(
            promotion_state=self.promotion_state,
            experiment_fingerprint=self.experiment_fingerprint,
            dataset_fingerprint=self.dataset_fingerprint,
            dataset_manifest_fingerprint=self.dataset_manifest_fingerprint,
            evaluation_fingerprint=self.evaluation_fingerprint,
            robustness_evidence_refs=self.robustness_evidence_refs,
            product_strategy=self.product_strategy,
            source_commit=self.source_commit,
            limitations=self.limitations,
        )):
            raise ValueError("promotion fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _promotion_payload(
            promotion_state=self.promotion_state,
            experiment_fingerprint=self.experiment_fingerprint,
            dataset_fingerprint=self.dataset_fingerprint,
            dataset_manifest_fingerprint=self.dataset_manifest_fingerprint,
            evaluation_fingerprint=self.evaluation_fingerprint,
            robustness_evidence_refs=self.robustness_evidence_refs,
            product_strategy=self.product_strategy,
            source_commit=self.source_commit,
            limitations=self.limitations,
        ) | {"promotion_fingerprint": self.promotion_fingerprint}


def canonical_promotion_json(artifact: ResearchPromotionArtifactV1) -> str:
    return json.dumps(artifact.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _evaluation_payload(split_id: str, wf: WalkForwardSpec,
                        costs: tuple[CostModel, ...], fill: str) -> dict[str, object]:
    return {
        "split_id": split_id,
        "walk_forward": {"train_days": wf.train_days, "oos_days": wf.oos_days, "step_days": wf.step_days},
        "cost_models": [{"name": item.name, "multiplier": item.multiplier} for item in costs],
        "fill_assumption": fill,
    }


def _experiment_payload(manifest: ExperimentManifest, strategy_id: str,
                        strategy_version: str, strategy_fingerprint: str,
                        config_fingerprint: str, dataset_manifest_fingerprint: str,
                        evaluation: EvaluationContractV1, evidence: tuple[str, ...],
                        source_commit: str, limitations: tuple[str, ...]) -> dict[str, object]:
    return {
        "schema_version": EXPERIMENT_SCHEMA,
        "manifest": {
            "experiment_id": manifest.experiment_id,
            "hypothesis": manifest.hypothesis,
            "status": manifest.status.value,
            "baseline": manifest.baseline,
            "parameters": _json_safe(manifest.parameters),
            "data_fingerprint": manifest.data_fingerprint,
            "engine_fingerprint": manifest.engine_fingerprint,
        },
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "strategy_fingerprint": strategy_fingerprint,
        "config_fingerprint": config_fingerprint,
        "dataset_manifest_fingerprint": dataset_manifest_fingerprint,
        "evaluation_fingerprint": evaluation.fingerprint,
        "robustness_evidence_refs": list(evidence),
        "source_commit": source_commit,
        "limitations": list(limitations),
    }


def _product_payload(experiment: ResearchExperimentV1) -> dict[str, object]:
    return {
        "schema_version": PRODUCT_ARTIFACT_SCHEMA,
        "strategy_id": experiment.strategy_id,
        "strategy_version": experiment.strategy_version,
        "strategy_fingerprint": experiment.strategy_fingerprint,
        "config_fingerprint": experiment.config_fingerprint,
        "source_experiment_fingerprint": experiment.experiment_fingerprint,
        "source_commit": experiment.source_commit,
    }


def _promotion_payload(*, promotion_state: PromotionState, experiment_fingerprint: str,
                       dataset_fingerprint: str, dataset_manifest_fingerprint: str,
                       evaluation_fingerprint: str, robustness_evidence_refs: tuple[str, ...],
                       product_strategy: ProductStrategyArtifactV1, source_commit: str,
                       limitations: tuple[str, ...]) -> dict[str, object]:
    return {
        "schema_version": PROMOTION_SCHEMA,
        "promotion_state": promotion_state.value,
        "experiment_fingerprint": experiment_fingerprint,
        "dataset_fingerprint": dataset_fingerprint,
        "dataset_manifest_fingerprint": dataset_manifest_fingerprint,
        "evaluation_fingerprint": evaluation_fingerprint,
        "robustness_evidence_refs": list(robustness_evidence_refs),
        "product_strategy": _product_payload_from_artifact(product_strategy),
        "source_commit": source_commit,
        "limitations": list(limitations),
        "execution_capability": "NONE",
        "order_execution_authorized": False,
        "paper_authorized": False,
        "live_authorized": False,
    }


def _product_payload_from_artifact(item: ProductStrategyArtifactV1) -> dict[str, object]:
    return {
        "schema_version": item.schema_version,
        "strategy_id": item.strategy_id,
        "strategy_version": item.strategy_version,
        "strategy_fingerprint": item.strategy_fingerprint,
        "config_fingerprint": item.config_fingerprint,
        "source_experiment_fingerprint": item.source_experiment_fingerprint,
        "source_commit": item.source_commit,
        "artifact_fingerprint": item.artifact_fingerprint,
    }


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    except (TypeError, ValueError) as exc:
        raise ValueError("experiment parameters must be canonical JSON values") from exc


def _fp(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(text.encode("utf-8")).hexdigest()


def _token(value: str, name: str) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a non-empty normalized token")


def _sha(value: str, name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be sha256 hex") from exc


def _commit(value: str) -> None:
    if len(value) != 40:
        raise ValueError("source_commit must be a full 40-character Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("source_commit must be hex") from exc


def _nonempty_tuple(values: tuple[str, ...], name: str) -> None:
    if not values or any(not value.strip() or value != value.strip() for value in values):
        raise ValueError(f"{name} must contain normalized non-empty values")
