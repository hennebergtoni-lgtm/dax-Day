from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from daxlab.runtime import demo_transport_attempt_reservation as reservation_owner
from daxlab.runtime import mt5_demo_evidence_transport as owner
from daxlab.runtime.broker_order_lifecycle import BrokerOrderState
from daxlab.runtime.demo_evidence_authorization import DemoAccountMode
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
import test_demo_transport_attempt_reservation as evidence
from test_demo_transport_query_request import FixedClock

prepared_attempt = evidence.prepared_attempt

LOGIN = 12345678
ACCOUNT_FINGERPRINT = sha256(
    f"DAXLAB:MT5:ACCOUNT_ID:V1:{LOGIN}".encode("utf-8")
).hexdigest()


class FakeMt5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_CONTEST = 1
    ACCOUNT_TRADE_MODE_REAL = 2

    ORDER_STATE_STARTED = 10
    ORDER_STATE_REQUEST_ADD = 11
    ORDER_STATE_PLACED = 12
    ORDER_STATE_PARTIAL = 13
    ORDER_STATE_FILLED = 14
    ORDER_STATE_CANCELED = 15
    ORDER_STATE_REJECTED = 16
    ORDER_STATE_EXPIRED = 17

    def __init__(
        self,
        *,
        account_mode=ACCOUNT_TRADE_MODE_DEMO,
        server="Demo-Server",
        trade_allowed=True,
        open_orders=(),
        history_orders=(),
        history_deals=(),
    ):
        self.account = SimpleNamespace(
            login=LOGIN,
            server=server,
            trade_mode=account_mode,
            trade_allowed=trade_allowed,
        )
        self.open_orders = open_orders
        self.history_orders = history_orders
        self.history_deals = history_deals
        self.calls = []

    def account_info(self):
        self.calls.append(("account_info",))
        return self.account

    def orders_get(self, *, symbol):
        self.calls.append(("orders_get", symbol))
        return self.open_orders

    def history_orders_get(self, start, end, *, group):
        self.calls.append(("history_orders_get", start, end, group))
        return self.history_orders

    def history_deals_get(self, start, end, *, group):
        self.calls.append(("history_deals_get", start, end, group))
        return self.history_deals


def _reservation(prepared_attempt):
    store, prepared = prepared_attempt
    raw = evidence._raw_bundle(account_fingerprint=ACCOUNT_FINGERPRINT)
    bundle = parse_windows_mt5_bundle(raw)
    authorization = replace(evidence._authorization(), account_id=ACCOUNT_FINGERPRINT)
    reservation = evidence._reserve(
        store,
        prepared,
        authorization=authorization,
        bundle=bundle,
    )
    return store, prepared, reservation


def _lookup(prepared_attempt):
    store, prepared, reservation = _reservation(prepared_attempt)
    query = reservation_owner.build_reserved_demo_transport_query_request(
        store=store,
        key="attempt",
        expected_reservation_fingerprint=reservation.fingerprint,
        bundle_payload=evidence._raw_bundle(account_fingerprint=ACCOUNT_FINGERPRINT),
        clock=FixedClock(reservation.evaluated_at),
    )
    request = owner.build_demo_mt5_lookup_request(
        reservation=reservation,
        query_request=query,
        history_from=reservation.prepared.broker.lifecycle.last_event_time
        - timedelta(minutes=1),
        history_to=reservation.evaluated_at + timedelta(minutes=1),
    )
    return store, prepared, reservation, query, request


def _order(request, mt5, *, ticket=101, state=None, volume_current=None, **changes):
    if state is None:
        state = mt5.ORDER_STATE_PLACED
    if volume_current is None:
        volume_current = request.requested_quantity
    values = dict(
        ticket=ticket,
        symbol=request.identity.symbol,
        magic=request.identity.magic,
        comment=request.identity.comment,
        state=state,
        volume_initial=request.requested_quantity,
        volume_current=volume_current,
    )
    values.update(changes)
    return SimpleNamespace(**values)


def _deal(request, *, order=101, ticket=501, volume=1.0, price=25000.0, **changes):
    values = dict(
        ticket=ticket,
        order=order,
        symbol=request.identity.symbol,
        magic=request.identity.magic,
        comment=request.identity.comment,
        volume=volume,
        price=price,
    )
    values.update(changes)
    return SimpleNamespace(**values)


def test_transport_identity_and_draft_are_deterministic_but_never_authorized(prepared_attempt):
    _, prepared, reservation = _reservation(prepared_attempt)
    first = owner.derive_demo_mt5_transport_identity(
        client_order_id=prepared.intent.intent_id,
        symbol="DE40",
    )
    assert owner.derive_demo_mt5_transport_identity(
        client_order_id=prepared.intent.intent_id,
        symbol="DE40",
    ) == first
    assert 1 <= first.magic <= 2_147_483_647
    assert first.comment.startswith("DXE1-")
    assert prepared.intent.intent_id not in first.comment
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False

    draft = owner.build_demo_mt5_transport_draft(reservation)
    assert draft.identity == first
    assert draft.reservation_fingerprint == reservation.fingerprint
    assert draft.prepared_fingerprint == reservation.prepared_fingerprint
    assert draft.submission_ordinal == reservation.submission_ordinal
    assert draft.side == "BUY"
    assert draft.quantity == prepared.intent.quantity
    assert draft.broker_submission_authorized is False
    assert draft.execution_capability == "NONE"
    assert draft.order_execution_enabled is False


def test_lookup_request_roundtrip_and_cross_wiring_fail_closed(prepared_attempt):
    _, _, reservation, query, request = _lookup(prepared_attempt)
    payload = owner.demo_mt5_lookup_request_to_payload(request)
    assert owner.demo_mt5_lookup_request_from_payload(payload) == request
    tampered = dict(payload)
    tampered["requested_quantity"] = request.requested_quantity + 1
    with pytest.raises(ValueError, match="fingerprint"):
        owner.demo_mt5_lookup_request_from_payload(tampered)

    bad_query = dict(query)
    bad_query["client_order_id"] = "d" * 64
    unsigned = dict(bad_query)
    unsigned.pop("query_request_fingerprint")
    bad_query["query_request_fingerprint"] = reservation_owner._fingerprint(unsigned)
    with pytest.raises(ValueError, match="client_order_id"):
        owner.build_demo_mt5_lookup_request(
            reservation=reservation,
            query_request=bad_query,
            history_from=request.history_from,
            history_to=request.history_to,
        )


def test_not_found_checks_open_history_and_deals_but_never_allows_retry(prepared_attempt):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.NOT_FOUND
    assert result.venue_observation is None
    assert result.blockers == ("VENUE_ORDER_NOT_FOUND_ACROSS_OPEN_AND_HISTORY",)
    assert not result.resubmit_allowed and not result.session_slot_release_allowed
    assert [call[0] for call in mt5.calls] == [
        "account_info",
        "orders_get",
        "history_orders_get",
        "history_deals_get",
        "account_info",  # Context must still match after all reads.
    ]


def test_exact_open_order_match_normalizes_ack_without_fill(prepared_attempt):
    _, prepared, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.open_orders = (_order(request, mt5),)
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.MATCHED
    venue = result.venue_observation
    assert venue is not None
    assert venue.client_order_id == prepared.intent.intent_id
    assert venue.venue_order_id == "101"
    assert venue.venue_state == BrokerOrderState.ACK.value
    assert venue.requested_quantity == request.requested_quantity
    assert venue.cumulative_filled_quantity == 0
    assert venue.average_fill_price is None
    assert venue.execution_capability == "NONE"
    assert venue.order_execution_enabled is False


def test_filled_history_requires_and_aggregates_deal_evidence(prepared_attempt):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (
        _order(
            request,
            mt5,
            state=mt5.ORDER_STATE_FILLED,
            volume_current=0.0,
        ),
    )
    mt5.history_deals = (
        _deal(request, volume=1.0, price=25000.0, ticket=501),
        _deal(request, volume=1.5, price=25002.0, ticket=502),
    )
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.MATCHED
    venue = result.venue_observation
    assert venue is not None
    assert venue.venue_state == BrokerOrderState.FILLED.value
    assert venue.cumulative_filled_quantity == pytest.approx(2.5)
    assert venue.average_fill_price == pytest.approx((1 * 25000 + 1.5 * 25002) / 2.5)
    assert result.matching_deal_tickets == ("501", "502")


def test_same_transport_tag_on_multiple_tickets_is_ambiguous(prepared_attempt):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (
        _order(request, mt5, ticket=101),
        _order(request, mt5, ticket=102),
    )
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.AMBIGUOUS
    assert result.matching_order_tickets == ("101", "102")
    assert result.venue_observation is None
    assert not result.resubmit_allowed


@pytest.mark.parametrize(
    ("account_mode", "server", "trade_allowed"),
    [
        (FakeMt5.ACCOUNT_TRADE_MODE_REAL, "Demo-Server", True),
        (FakeMt5.ACCOUNT_TRADE_MODE_DEMO, "Other-Server", True),
        (FakeMt5.ACCOUNT_TRADE_MODE_DEMO, "Demo-Server", False),
    ],
)
def test_account_context_is_rechecked_before_any_order_query(
    prepared_attempt, account_mode, server, trade_allowed
):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5(
        account_mode=account_mode,
        server=server,
        trade_allowed=trade_allowed,
    )
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.BLOCKED
    assert result.blockers == ("MT5_ACCOUNT_CONTEXT_MISMATCH",)
    assert mt5.calls == [("account_info",)]


@pytest.mark.parametrize("surface", ["orders_get", "history_orders_get", "history_deals_get"])
def test_readonly_query_failure_is_blocked(prepared_attempt, surface):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    setattr(mt5, surface, lambda *args, **kwargs: None)
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.status is owner.DemoMt5LookupStatus.BLOCKED
    assert result.venue_observation is None
    assert not result.resubmit_allowed and not result.session_slot_release_allowed


def test_order_quantity_and_fill_cross_wiring_block(prepared_attempt):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (
        _order(request, mt5, volume_initial=request.requested_quantity + 1),
    )
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.blockers == ("MT5_MATCHED_ORDER_QUANTITY_MISMATCH",)

    mt5 = FakeMt5()
    mt5.history_orders = (
        _order(request, mt5, state=mt5.ORDER_STATE_PARTIAL, volume_current=1.5),
    )
    mt5.history_deals = (_deal(request, volume=0.5, price=25000.0),)
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.blockers == ("MT5_ORDER_DEAL_FILL_EVIDENCE_MISMATCH",)


def test_deal_identity_and_unsupported_state_fail_closed(prepared_attempt):
    _, _, _, _, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (
        _order(request, mt5, state=mt5.ORDER_STATE_PARTIAL, volume_current=1.5),
    )
    mt5.history_deals = (
        _deal(request, volume=1.0, price=25000.0, magic=request.identity.magic + 1),
    )
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.blockers == ("MT5_DEAL_IDENTITY_MISMATCH",)

    mt5 = FakeMt5()
    mt5.history_orders = (_order(request, mt5, state=999999),)
    result = owner.query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=request.query_evaluated_at,
    )
    assert result.blockers == ("MT5_ORDER_STATE_UNSUPPORTED",)


def test_step_2200_owner_has_no_sdk_import_or_submission_call():
    source = Path(owner.__file__).read_text()
    tree = ast.parse(source)
    forbidden_calls = {
        "order_send",
        "order_check",
        "submit_order",
        "send_order",
        "place_order",
        "cancel_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
            )
            assert all(name.split(".")[0] != "MetaTrader5" for name in modules)
        if isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            assert name not in forbidden_calls
        if isinstance(node, ast.keyword) and node.arg == "order_execution_enabled":
            assert not (isinstance(node.value, ast.Constant) and node.value.value is True)


def test_account_mode_expectation_is_demo_in_fixture(prepared_attempt):
    _, _, reservation = _reservation(prepared_attempt)
    assert reservation.account_context.account_mode is DemoAccountMode.DEMO


def test_duplicate_half_fill_cannot_fabricate_complete_fill(prepared_attempt):
    *_, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    deal = _deal(request, volume=request.requested_quantity / 2)
    mt5.history_orders = (_order(request, mt5, state=mt5.ORDER_STATE_FILLED, volume_current=0),)
    mt5.history_deals = (deal, deal)
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.status is owner.DemoMt5LookupStatus.BLOCKED
    assert result.blockers == ('MT5_ORDER_DEAL_FILL_EVIDENCE_MISMATCH',)
    assert result.venue_observation is None


def test_duplicate_and_reordered_deals_preserve_original_unique_venue_evidence(prepared_attempt):
    *_, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (_order(request, mt5, state=mt5.ORDER_STATE_FILLED, volume_current=0),)
    a = _deal(request, ticket=501, volume=1, price=25000)
    b = _deal(request, ticket=502, volume=1.5, price=25001)
    mt5.history_deals = (a, b)
    original = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    mt5.history_deals = (b, a, b, a)
    replay = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert replay.status is owner.DemoMt5LookupStatus.MATCHED
    assert replay.venue_observation == original.venue_observation
    assert replay.venue_observation.fingerprint == original.venue_observation.fingerprint
    assert replay.matching_deal_tickets == ('501', '502')
    assert replay.history_deal_count == 4


@pytest.mark.parametrize('field,value', [('volume', 2), ('price', 25002), ('time_msc', 1), ('type', 1), ('position_id', 123)])
def test_contradictory_duplicate_deal_ticket_fails_closed(prepared_attempt, field, value):
    *_, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (_order(request, mt5, state=mt5.ORDER_STATE_FILLED, volume_current=0),)
    mt5.history_deals = (_deal(request, volume=2.5), _deal(request, **({'volume': 2.5} | {field: value})))
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.blockers == ('MT5_DUPLICATE_DEAL_TICKET_CONTRADICTION',)
    assert result.venue_observation is None


@pytest.mark.parametrize('ticket', [None, 0, -1, True])
def test_matched_deal_without_stable_ticket_fails_closed(prepared_attempt, ticket):
    *_, request = _lookup(prepared_attempt)
    mt5 = FakeMt5()
    mt5.history_orders = (_order(request, mt5, state=mt5.ORDER_STATE_FILLED, volume_current=0),)
    mt5.history_deals = (_deal(request, ticket=ticket, volume=2.5),)
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.blockers == ('MT5_MATCHED_DEAL_TICKET_INVALID',)
    assert result.venue_observation is None


@pytest.mark.parametrize('field,value', [('trade_mode', FakeMt5.ACCOUNT_TRADE_MODE_REAL), ('login', LOGIN + 1), ('server', 'Other-Demo'), ('trade_allowed', False)])
@pytest.mark.parametrize('has_match', [True, False])
def test_account_switch_during_query_never_labels_rows_as_original_demo(prepared_attempt, field, value, has_match):
    *_, request = _lookup(prepared_attempt)

    class SwitchingMt5(FakeMt5):
        def history_deals_get(self, *args, **kwargs):
            result = super().history_deals_get(*args, **kwargs)
            setattr(self.account, field, value)
            return result

    mt5 = SwitchingMt5()
    if has_match:
        mt5.open_orders = (_order(request, mt5),)
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.status is owner.DemoMt5LookupStatus.BLOCKED
    assert result.blockers == ('MT5_ACCOUNT_CONTEXT_CHANGED_DURING_QUERY',)
    assert result.venue_observation is None
    assert result.matching_order_tickets == ()


@pytest.mark.parametrize('final', [None, SimpleNamespace(login=True), 'error'])
def test_failed_account_recheck_never_becomes_empty_account_or_matched(prepared_attempt, final):
    *_, request = _lookup(prepared_attempt)

    class FailedRecheck(FakeMt5):
        def account_info(self):
            if self.calls:
                if final == 'error':
                    raise RuntimeError('password=never-print')
                return final
            return super().account_info()

    mt5 = FailedRecheck()
    result = owner.query_mt5_demo_evidence(mt5=mt5, request=request, observed_at=request.query_evaluated_at)
    assert result.status is owner.DemoMt5LookupStatus.BLOCKED
    assert result.venue_observation is None
    assert 'never-print' not in str(result.to_payload())
