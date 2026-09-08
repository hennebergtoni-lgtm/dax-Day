import pytest

from daxlab.research.filter_registry import (
    ControlMode,
    EvidenceStatus,
    FilterCapability,
    FilterRegistry,
    default_research_registry,
)


def test_research_filters_are_visible_only():
    registry = default_research_registry()
    for key in ("bb001", "fib001", "gap001", "prev_range_atr"):
        item = registry.get(key)
        assert item.evidence_status is EvidenceStatus.RESEARCH
        assert item.allowed_modes == (ControlMode.VISIBLE_ONLY,)
        assert not item.default_enabled


def test_research_filter_cannot_be_live_switchable():
    with pytest.raises(ValueError):
        FilterRegistry(
            [
                FilterCapability(
                    key="bad",
                    label="bad",
                    evidence_status=EvidenceStatus.RESEARCH,
                    allowed_modes=(ControlMode.MANUAL,),
                )
            ]
        )


def test_validated_filter_cannot_auto_switch_before_deployable_promotion():
    with pytest.raises(ValueError):
        FilterRegistry(
            [
                FilterCapability(
                    key="bad_auto",
                    label="bad_auto",
                    evidence_status=EvidenceStatus.VALIDATED,
                    allowed_modes=(ControlMode.REGIME_AUTOMATIC,),
                )
            ]
        )


def test_deployable_filter_can_support_manual_and_regime_auto_modes():
    registry = FilterRegistry(
        [
            FilterCapability(
                key="ready",
                label="ready",
                evidence_status=EvidenceStatus.DEPLOYABLE,
                allowed_modes=(ControlMode.MANUAL, ControlMode.REGIME_AUTOMATIC),
            )
        ]
    )
    ready = registry.get("ready")
    assert ready.can_use(ControlMode.MANUAL)
    assert ready.can_use(ControlMode.REGIME_AUTOMATIC)


def test_duplicate_filter_keys_are_rejected():
    item = FilterCapability(
        key="x",
        label="x",
        evidence_status=EvidenceStatus.RESEARCH,
        allowed_modes=(ControlMode.VISIBLE_ONLY,),
    )
    with pytest.raises(ValueError):
        FilterRegistry([item, item])
