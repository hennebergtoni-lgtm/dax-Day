from __future__ import annotations

from pathlib import Path

from daxlab.runtime.readiness import ReadinessSnapshot


REPO_ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_canonical_risk_owner_does_not_import_research_policy_owners() -> None:
    source = _source("src/daxlab/domain/risk.py")
    assert "daxlab.research" not in source
    assert "RiskProfile" not in source
    assert "RiskProfileBudgetSpec" not in source
    assert "LOSS_CAP_GATE_RESEARCH_VERSION" not in source


def test_canonical_risk_owner_does_not_embed_research_profile_names() -> None:
    source = _source("src/daxlab/domain/risk.py")
    for token in ('"BASE"', '"BOOST"', '"HIGH"'):
        assert token not in source


def test_paper_policy_verification_gates_remain_explicit_false_by_default() -> None:
    snapshot = ReadinessSnapshot(
        ci_green=False,
        dataset_verified=False,
        engine_verified=False,
        database_verified=False,
        technical_replay_verified=False,
        audited_bundle_available=False,
        full_reference_replay_verified=False,
    )
    assert snapshot.broker_economics_verified is False
    assert snapshot.broker_risk_sizing_verified is False
    assert snapshot.risk_profile_policy_verified is False
    assert snapshot.loss_cap_policy_verified is False
    assert snapshot.paper_user_authorized is False


def test_research_risk_owners_remain_explicitly_research_only() -> None:
    profile = _source("src/daxlab/research/risk_profile_sizing.py")
    loss_cap = _source("src/daxlab/research/loss_cap_gate.py")

    assert "RESEARCH-ONLY" in profile.upper()
    assert "RESEARCH" in loss_cap.upper()
    assert 'execution_capability: str = "NONE"' in profile
    assert 'order_execution_enabled: bool = False' in profile
    assert 'execution_capability: str = "NONE"' in loss_cap
    assert 'order_execution_enabled: bool = False' in loss_cap
