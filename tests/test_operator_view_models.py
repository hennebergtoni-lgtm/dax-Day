import pytest

from daxlab.operator.view_models import HealthState, filter_card, reference_health
from daxlab.research.filter_registry import default_research_registry


def test_research_filter_card_is_visible_but_not_enabled() -> None:
    capability = default_research_registry().get("fib001")
    card = filter_card(capability, provenance="FIB001/PLAN.md")
    assert card.evidence_status == "research"
    assert card.allowed_modes == ("visible_only",)
    assert not card.enabled


def test_operator_read_model_cannot_enable_research_filter() -> None:
    capability = default_research_registry().get("gap001")
    with pytest.raises(ValueError, match="cannot enable"):
        filter_card(capability, provenance="GAP001/PLAN.md", enabled=True)


def test_current_reference_health_is_amber_not_green() -> None:
    health = reference_health(
        active_reference="V112_REFERENCE_V1",
        dataset_verified=True,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        full_reference_replay_verified=False,
        detailed_rows_imported=False,
    )
    assert health.state is HealthState.AMBER
    assert health.blockers == (
        "FULL_REFERENCE_REPLAY_PENDING",
        "DETAIL_ROWS_NOT_IMPORTED",
    )


def test_critical_health_failure_is_red() -> None:
    health = reference_health(
        active_reference="V112_REFERENCE_V1",
        dataset_verified=False,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        full_reference_replay_verified=False,
        detailed_rows_imported=False,
    )
    assert health.state is HealthState.RED
    assert "DATASET_UNVERIFIED" in health.blockers
