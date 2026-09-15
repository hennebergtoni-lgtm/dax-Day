from __future__ import annotations

from hashlib import sha256
import json

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.runtime.ig_predemo_safety import (
    IgTransportObservation,
    bind_ig_risk_session_inputs,
    ig_lifecycle_directive,
)


SHA = "a" * 64


def evidence(*, complete: bool) -> dict:
    market = {
        "quantity_min": 1.0,
        "quantity_step": 1.0 if complete else None,
        "quantity_max": 10.0 if complete else None,
        "tick_size": 1.0 if complete else None,
        "cash_per_tick_per_quantity": 1.0 if complete else None,
        "economics_verified": complete,
        "native_stop_constraints_verified": complete,
    }
    value = {
        "schema": "DAXLAB_IG_PREDEMO_READINESS_V1",
        "environment": "IG_DEMO",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "account": {"currency": "EUR", "account_context_fingerprint": SHA},
        "market": market,
        "inventory": {
            "stable_inventory_fingerprint": SHA,
            "stable_across_bracket": True,
            "foreign_or_manual_inventory_present": False,
            "history_scope_complete": True,
        },
    }
    value["fingerprint"] = sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()
    return value


def test_incomplete_realistic_ig_metadata_blocks_canonical_risk_binding() -> None:
    binding = bind_ig_risk_session_inputs(evidence(complete=False), instrument_id=InstrumentId("DAX"))
    assert binding.instrument is None
    assert "QUANTITY_INCREMENT_UNVERIFIED" in binding.blockers
    assert "MAX_SIZE_UNVERIFIED" in binding.blockers
    assert "TICK_SIZE_UNVERIFIED" in binding.blockers
    assert binding.execution_capability == "NONE"
    assert binding.order_execution_enabled is False


def test_complete_source_bound_values_reuse_canonical_risk_inputs() -> None:
    binding = bind_ig_risk_session_inputs(evidence(complete=True), instrument_id=InstrumentId("DAX"))
    assert binding.admission_inputs_complete
    assert binding.instrument.quantity_step == 1.0
    assert binding.instrument.cash_loss_per_price_unit_per_quantity == 1.0


@pytest.mark.parametrize(
    ("observation", "action", "terminal"),
    [
        (IgTransportObservation.TIMEOUT, "QUERY_REQUIRED", False),
        (IgTransportObservation.UNKNOWN, "QUERY_REQUIRED", False),
        (IgTransportObservation.REQUEST_SENT, "QUERY_REQUIRED", False),
        (IgTransportObservation.PARTIAL, "RECONCILE_REQUIRED", False),
        (IgTransportObservation.DUPLICATE, "RECONCILE_REQUIRED", False),
        (IgTransportObservation.OUT_OF_ORDER, "RECONCILE_REQUIRED", False),
        (IgTransportObservation.REJECT, "RECONCILE_TERMINAL_EVIDENCE", True),
        (IgTransportObservation.FILLED, "RECONCILE_TERMINAL_EVIDENCE", True),
    ],
)
def test_native_ig_lifecycle_never_retries_or_releases_slot(observation, action, terminal) -> None:
    directive = ig_lifecycle_directive(
        observation, reservation_present=True, broker_query_scope_complete=True
    )
    assert directive.next_action == action and directive.terminal_truth is terminal
    assert directive.resubmit_allowed is False
    assert directive.session_slot_release_allowed is False
    assert directive.execution_capability == "NONE"


def test_terminal_report_without_complete_broker_scope_is_not_terminal_truth() -> None:
    directive = ig_lifecycle_directive(
        IgTransportObservation.FILLED,
        reservation_present=True,
        broker_query_scope_complete=False,
    )
    assert directive.next_action == "QUERY_REQUIRED"
    assert directive.terminal_truth is False


def test_missing_reservation_blocks_every_post_prepare_transport_observation() -> None:
    directive = ig_lifecycle_directive(
        IgTransportObservation.ACK,
        reservation_present=False,
        broker_query_scope_complete=True,
    )
    assert directive.next_action == "BLOCK_MISSING_ATTEMPT_RESERVATION"
    assert directive.resubmit_allowed is False


def test_evidence_tampering_and_live_context_fail_closed() -> None:
    payload = evidence(complete=True)
    payload["environment"] = "LIVE"
    with pytest.raises(ValueError, match="environment mismatch"):
        bind_ig_risk_session_inputs(payload, instrument_id=InstrumentId("DAX"))


@pytest.mark.parametrize("flag", [0, 1, None, "false", "", [], {}])
def test_ig_binding_and_lifecycle_require_typed_false(flag) -> None:
    from daxlab.runtime.ig_predemo_safety import IgLifecycleDirective, IgRiskSessionBinding

    with pytest.raises(ValueError, match="cannot authorize"):
        IgRiskSessionBinding(
            source_fingerprint=SHA, instrument=None, account_context_fingerprint=None,
            inventory_fingerprint=None, blockers=("UNKNOWN",), order_execution_enabled=flag,
        )
    with pytest.raises(ValueError, match="cannot authorize"):
        IgLifecycleDirective(
            observation=IgTransportObservation.ACK, next_action="WAIT_OR_QUERY",
            terminal_truth=False, order_execution_enabled=flag,
        )
