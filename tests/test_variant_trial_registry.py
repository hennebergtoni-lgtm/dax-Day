from dataclasses import replace

import pytest

from daxlab.research.variant_trial_registry import (
    GENESIS_HASH,
    PREDECLARED,
    RETROACTIVE,
    declare_trial,
    registry_payload,
    verify_trial_chain,
)


def _declare(rows, trial_id="VT001", mode=PREDECLARED, params=None):
    return declare_trial(
        rows,
        trial_id=trial_id,
        experiment_id="EXP001",
        hypothesis_trial_id="T012",
        family_id="ADX001",
        variant_key=f"ADX001:{trial_id}",
        parameters=params or {"adx_min": 20, "period": 14},
        declared_at_utc="2026-09-10T03:40:00Z",
        declaration_mode=mode,
        source_commit="a" * 40,
    )


def test_single_predeclared_trial_starts_from_genesis():
    row = _declare([])
    assert row.previous_hash == GENESIS_HASH
    assert row.independently_predeclared is True
    assert verify_trial_chain([row]) == row.record_hash


def test_second_trial_links_to_first_hash():
    first = _declare([], "VT001")
    second = _declare([first], "VT002")
    assert second.previous_hash == first.record_hash
    assert verify_trial_chain([first, second]) == second.record_hash


def test_parameter_mutation_breaks_hash_chain():
    row = _declare([])
    tampered = replace(row, parameters={"adx_min": 99, "period": 14})
    with pytest.raises(ValueError, match="record_hash mismatch"):
        verify_trial_chain([tampered])


def test_removing_middle_row_breaks_following_link():
    first = _declare([], "VT001")
    second = _declare([first], "VT002")
    third = _declare([first, second], "VT003")
    with pytest.raises(ValueError, match="previous_hash"):
        verify_trial_chain([first, third])


def test_duplicate_trial_id_rejected():
    first = _declare([], "VT001")
    with pytest.raises(ValueError, match="unique"):
        _declare([first], "VT001")


def test_non_utc_declaration_rejected():
    with pytest.raises(ValueError, match="UTC"):
        declare_trial(
            [],
            trial_id="VT001",
            experiment_id="EXP001",
            hypothesis_trial_id="T012",
            family_id="ADX001",
            variant_key="ADX001:VT001",
            parameters={"period": 14},
            declared_at_utc="2026-09-10T05:40:00+02:00",
            declaration_mode=PREDECLARED,
            source_commit="a" * 40,
        )


def test_retroactive_trial_is_never_counted_as_predeclared():
    row = _declare([], mode=RETROACTIVE)
    payload = registry_payload([row])
    assert row.independently_predeclared is False
    assert payload["predeclared_trial_ids"] == []
    assert payload["trial_count"] == 1


def test_registry_payload_exposes_only_true_predeclarations():
    first = _declare([], "VT001", PREDECLARED)
    second = _declare([first], "VT002", RETROACTIVE)
    payload = registry_payload([first, second])
    assert payload["append_only"] is True
    assert payload["hash_chain"] == "SHA256_PREVIOUS_HASH"
    assert payload["head_hash"] == second.record_hash
    assert payload["predeclared_trial_ids"] == ["VT001"]


def test_unsupported_declaration_mode_rejected():
    with pytest.raises(ValueError, match="declaration_mode"):
        _declare([], mode="POST_HOC_WINNER")
