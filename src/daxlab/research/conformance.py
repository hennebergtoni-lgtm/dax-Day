"""Research-to-product conformance proof for DAX-BOT NextGen.

Conformance proves semantic identity for one frozen fixture. It does not claim
profitability and never authorizes PAPER, LIVE or broker execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from daxlab.engine.replay import ReplayResult
from daxlab.research.promotion import ResearchPromotionArtifactV1

RESEARCH_DECISION_ARTIFACT_SCHEMA = "DAXLAB_RESEARCH_EXPECTED_DECISIONS_V1"
CONFORMANCE_SCHEMA = "DAXLAB_RESEARCH_PRODUCT_CONFORMANCE_V1"


class ConformanceMismatch(ValueError):
    """Raised when frozen research semantics do not match product replay."""


@dataclass(frozen=True, slots=True)
class ResearchExpectedDecisionsV1:
    """Frozen expected product-level decisions produced by one research fixture."""

    fixture_id: str
    source_experiment_fingerprint: str
    strategy_id: str
    strategy_version: str
    strategy_fingerprint: str
    config_fingerprint: str
    dataset_fingerprint: str
    dataset_manifest_fingerprint: str
    replay_input_fingerprint: str
    expected_decision_ids: tuple[str, ...]
    expected_decision_ids_fingerprint: str
    source_reference: str
    artifact_fingerprint: str
    schema_version: str = RESEARCH_DECISION_ARTIFACT_SCHEMA

    @classmethod
    def build(
        cls,
        *,
        fixture_id: str,
        source_experiment_fingerprint: str,
        strategy_id: str,
        strategy_version: str,
        strategy_fingerprint: str,
        config_fingerprint: str,
        dataset_fingerprint: str,
        dataset_manifest_fingerprint: str,
        replay_input_fingerprint: str,
        expected_decision_ids: tuple[str, ...],
        source_reference: str,
    ) -> "ResearchExpectedDecisionsV1":
        decisions_fp = _fingerprint(expected_decision_ids)
        values = dict(
            fixture_id=fixture_id,
            source_experiment_fingerprint=source_experiment_fingerprint,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            strategy_fingerprint=strategy_fingerprint,
            config_fingerprint=config_fingerprint,
            dataset_fingerprint=dataset_fingerprint,
            dataset_manifest_fingerprint=dataset_manifest_fingerprint,
            replay_input_fingerprint=replay_input_fingerprint,
            expected_decision_ids=expected_decision_ids,
            expected_decision_ids_fingerprint=decisions_fp,
            source_reference=source_reference,
        )
        return cls(**values, artifact_fingerprint=_fingerprint(_research_payload(**values)))

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_DECISION_ARTIFACT_SCHEMA:
            raise ValueError("unsupported research expected-decision artifact schema")
        for name, value in (
            ("fixture_id", self.fixture_id),
            ("strategy_id", self.strategy_id),
            ("strategy_version", self.strategy_version),
            ("source_reference", self.source_reference),
        ):
            _require_token(value, name)
        for name, value in (
            ("source_experiment_fingerprint", self.source_experiment_fingerprint),
            ("strategy_fingerprint", self.strategy_fingerprint),
            ("config_fingerprint", self.config_fingerprint),
            ("dataset_fingerprint", self.dataset_fingerprint),
            ("dataset_manifest_fingerprint", self.dataset_manifest_fingerprint),
            ("replay_input_fingerprint", self.replay_input_fingerprint),
            ("expected_decision_ids_fingerprint", self.expected_decision_ids_fingerprint),
            ("artifact_fingerprint", self.artifact_fingerprint),
        ):
            _require_sha256(value, name)
        if not self.expected_decision_ids:
            raise ValueError("expected_decision_ids must not be empty")
        for value in self.expected_decision_ids:
            _require_sha256(value, "expected decision id")
        if self.expected_decision_ids_fingerprint != _fingerprint(self.expected_decision_ids):
            raise ValueError("expected decision id fingerprint mismatch")
        if self.artifact_fingerprint != _fingerprint(_research_payload_from_artifact(self)):
            raise ValueError("research expected-decision artifact fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _research_payload_from_artifact(self) | {
            "artifact_fingerprint": self.artifact_fingerprint
        }


@dataclass(frozen=True, slots=True)
class ResearchProductConformanceV1:
    """Immutable proof that one research fixture matches one product replay."""

    fixture_id: str
    research_artifact_fingerprint: str
    promotion_fingerprint: str
    product_strategy_artifact_fingerprint: str
    replay_run_fingerprint: str
    replay_result_fingerprint: str
    decision_ids_fingerprint: str
    conformance_fingerprint: str
    status: str = "MATCH"
    execution_capability: str = "NONE"
    order_execution_authorized: bool = False
    paper_authorized: bool = False
    live_authorized: bool = False
    schema_version: str = CONFORMANCE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != CONFORMANCE_SCHEMA:
            raise ValueError("unsupported conformance schema")
        _require_token(self.fixture_id, "fixture_id")
        if self.status != "MATCH":
            raise ValueError("conformance artifact status must be MATCH")
        if self.execution_capability != "NONE":
            raise ValueError("conformance artifact has no execution capability")
        if self.order_execution_authorized or self.paper_authorized or self.live_authorized:
            raise ValueError("conformance artifact cannot authorize external execution")
        for name, value in (
            ("research_artifact_fingerprint", self.research_artifact_fingerprint),
            ("promotion_fingerprint", self.promotion_fingerprint),
            ("product_strategy_artifact_fingerprint", self.product_strategy_artifact_fingerprint),
            ("replay_run_fingerprint", self.replay_run_fingerprint),
            ("replay_result_fingerprint", self.replay_result_fingerprint),
            ("decision_ids_fingerprint", self.decision_ids_fingerprint),
            ("conformance_fingerprint", self.conformance_fingerprint),
        ):
            _require_sha256(value, name)
        if self.conformance_fingerprint != _fingerprint(_conformance_payload(self)):
            raise ValueError("conformance fingerprint mismatch")

    def to_dict(self) -> dict[str, object]:
        return _conformance_payload(self) | {
            "conformance_fingerprint": self.conformance_fingerprint
        }


def verify_research_product_conformance(
    *,
    promotion: ResearchPromotionArtifactV1,
    research: ResearchExpectedDecisionsV1,
    replay: ReplayResult[Any],
) -> ResearchProductConformanceV1:
    """Fail closed unless research provenance and product replay match exactly."""

    product = promotion.product_strategy
    _match(
        research.source_experiment_fingerprint,
        promotion.experiment_fingerprint,
        "source experiment fingerprint",
    )
    _match(research.strategy_id, product.strategy_id, "strategy id")
    _match(research.strategy_version, product.strategy_version, "strategy version")
    _match(research.strategy_fingerprint, product.strategy_fingerprint, "strategy fingerprint")
    _match(research.config_fingerprint, product.config_fingerprint, "config fingerprint")
    _match(research.dataset_fingerprint, promotion.dataset_fingerprint, "dataset fingerprint")
    _match(
        research.dataset_manifest_fingerprint,
        promotion.dataset_manifest_fingerprint,
        "dataset manifest fingerprint",
    )

    manifest = replay.manifest
    _match(manifest.strategy_id, product.strategy_id, "replay strategy id")
    _match(manifest.strategy_version, product.strategy_version, "replay strategy version")
    _match(manifest.strategy_fingerprint, product.strategy_fingerprint, "replay strategy fingerprint")
    _match(manifest.input_fingerprint, research.replay_input_fingerprint, "replay input fingerprint")

    observed_ids = tuple(item.decision_id for item in replay.decisions)
    if observed_ids != research.expected_decision_ids:
        raise ConformanceMismatch("ordered product decision ids do not match frozen research fixture")
    _match(
        replay.decision_ids_fingerprint,
        research.expected_decision_ids_fingerprint,
        "decision ids fingerprint",
    )
    if replay.execution_capability != "NONE" or replay.order_execution_enabled:
        raise ConformanceMismatch("product replay is not execution-neutral")
    if promotion.execution_capability != "NONE":
        raise ConformanceMismatch("promotion is not execution-neutral")
    if promotion.order_execution_authorized or promotion.paper_authorized or promotion.live_authorized:
        raise ConformanceMismatch("promotion unexpectedly authorizes external execution")

    values = dict(
        fixture_id=research.fixture_id,
        research_artifact_fingerprint=research.artifact_fingerprint,
        promotion_fingerprint=promotion.promotion_fingerprint,
        product_strategy_artifact_fingerprint=product.artifact_fingerprint,
        replay_run_fingerprint=manifest.run_fingerprint,
        replay_result_fingerprint=replay.result_fingerprint,
        decision_ids_fingerprint=replay.decision_ids_fingerprint,
    )
    identity = _conformance_values_payload(**values)
    return ResearchProductConformanceV1(
        **values,
        conformance_fingerprint=_fingerprint(identity),
    )


def canonical_research_decisions_json(artifact: ResearchExpectedDecisionsV1) -> str:
    return json.dumps(artifact.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def canonical_conformance_json(artifact: ResearchProductConformanceV1) -> str:
    return json.dumps(artifact.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _research_payload(
    *,
    fixture_id: str,
    source_experiment_fingerprint: str,
    strategy_id: str,
    strategy_version: str,
    strategy_fingerprint: str,
    config_fingerprint: str,
    dataset_fingerprint: str,
    dataset_manifest_fingerprint: str,
    replay_input_fingerprint: str,
    expected_decision_ids: tuple[str, ...],
    expected_decision_ids_fingerprint: str,
    source_reference: str,
) -> dict[str, object]:
    return {
        "schema_version": RESEARCH_DECISION_ARTIFACT_SCHEMA,
        "fixture_id": fixture_id,
        "source_experiment_fingerprint": source_experiment_fingerprint,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "strategy_fingerprint": strategy_fingerprint,
        "config_fingerprint": config_fingerprint,
        "dataset_fingerprint": dataset_fingerprint,
        "dataset_manifest_fingerprint": dataset_manifest_fingerprint,
        "replay_input_fingerprint": replay_input_fingerprint,
        "expected_decision_ids": list(expected_decision_ids),
        "expected_decision_ids_fingerprint": expected_decision_ids_fingerprint,
        "source_reference": source_reference,
    }


def _research_payload_from_artifact(artifact: ResearchExpectedDecisionsV1) -> dict[str, object]:
    return _research_payload(
        fixture_id=artifact.fixture_id,
        source_experiment_fingerprint=artifact.source_experiment_fingerprint,
        strategy_id=artifact.strategy_id,
        strategy_version=artifact.strategy_version,
        strategy_fingerprint=artifact.strategy_fingerprint,
        config_fingerprint=artifact.config_fingerprint,
        dataset_fingerprint=artifact.dataset_fingerprint,
        dataset_manifest_fingerprint=artifact.dataset_manifest_fingerprint,
        replay_input_fingerprint=artifact.replay_input_fingerprint,
        expected_decision_ids=artifact.expected_decision_ids,
        expected_decision_ids_fingerprint=artifact.expected_decision_ids_fingerprint,
        source_reference=artifact.source_reference,
    )


def _conformance_values_payload(
    *,
    fixture_id: str,
    research_artifact_fingerprint: str,
    promotion_fingerprint: str,
    product_strategy_artifact_fingerprint: str,
    replay_run_fingerprint: str,
    replay_result_fingerprint: str,
    decision_ids_fingerprint: str,
) -> dict[str, object]:
    return {
        "schema_version": CONFORMANCE_SCHEMA,
        "fixture_id": fixture_id,
        "research_artifact_fingerprint": research_artifact_fingerprint,
        "promotion_fingerprint": promotion_fingerprint,
        "product_strategy_artifact_fingerprint": product_strategy_artifact_fingerprint,
        "replay_run_fingerprint": replay_run_fingerprint,
        "replay_result_fingerprint": replay_result_fingerprint,
        "decision_ids_fingerprint": decision_ids_fingerprint,
        "status": "MATCH",
        "execution_capability": "NONE",
        "order_execution_authorized": False,
        "paper_authorized": False,
        "live_authorized": False,
    }


def _conformance_payload(artifact: ResearchProductConformanceV1) -> dict[str, object]:
    return _conformance_values_payload(
        fixture_id=artifact.fixture_id,
        research_artifact_fingerprint=artifact.research_artifact_fingerprint,
        promotion_fingerprint=artifact.promotion_fingerprint,
        product_strategy_artifact_fingerprint=artifact.product_strategy_artifact_fingerprint,
        replay_run_fingerprint=artifact.replay_run_fingerprint,
        replay_result_fingerprint=artifact.replay_result_fingerprint,
        decision_ids_fingerprint=artifact.decision_ids_fingerprint,
    )


def _match(observed: object, expected: object, name: str) -> None:
    if observed != expected:
        raise ConformanceMismatch(f"{name} mismatch")


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_token(value: str, field_name: str) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty normalized token")


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc
