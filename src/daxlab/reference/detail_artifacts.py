"""Canonical V11.2 clean-detail artifact specifications.

The trade ledger hash is intentionally classified as newly reproducible clean
evidence, not as recovered historical file identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DetailEvidenceIdentity(str, Enum):
    HISTORICAL_HASH_MATCH = "HISTORICAL_HASH_MATCH"
    NEW_REPRODUCIBLE_CLEAN_EVIDENCE = "NEW_REPRODUCIBLE_CLEAN_EVIDENCE"


@dataclass(frozen=True, slots=True)
class DetailArtifactSpec:
    detail_kind: str
    filename: str
    expected_rows: int
    sha256: str
    identity: DetailEvidenceIdentity


V112_CLEAN_DETAIL_ARTIFACTS: tuple[DetailArtifactSpec, ...] = (
    DetailArtifactSpec(
        detail_kind="WF_METRICS",
        filename="wf_metrics.csv",
        expected_rows=243,
        sha256="4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a",
        identity=DetailEvidenceIdentity.HISTORICAL_HASH_MATCH,
    ),
    DetailArtifactSpec(
        detail_kind="SELECTED_VARIANTS",
        filename="selected_variants.csv",
        expected_rows=81,
        sha256="8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e",
        identity=DetailEvidenceIdentity.HISTORICAL_HASH_MATCH,
    ),
    DetailArtifactSpec(
        detail_kind="TRADES",
        filename="trades_normal.csv",
        expected_rows=856,
        sha256="f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023",
        identity=DetailEvidenceIdentity.NEW_REPRODUCIBLE_CLEAN_EVIDENCE,
    ),
)


def artifact_spec(detail_kind: str) -> DetailArtifactSpec:
    for spec in V112_CLEAN_DETAIL_ARTIFACTS:
        if spec.detail_kind == detail_kind:
            return spec
    raise KeyError(detail_kind)
