from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Mapping

import pytest

from daxlab.adapters.ig_rest_readonly import (
    IG_DEMO_BASE_URL,
    IgDemoCredentials,
    IgDemoReadOnlyClient,
    IgReadOnlyError,
    JsonResponse,
)


@dataclass(slots=True)
class FakeTransport:
    responses: list[JsonResponse]
    calls: list[dict[str, object]] = field(default_factory=list)

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | None = None,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 20.0,
    ) -> JsonResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": None if body is None else dict(body),
                "query": None if query is None else dict(query),
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.responses.pop(0)


def _credentials() -> IgDemoCredentials:
    return IgDemoCredentials(
        identifier="demo-user",
        password="super-secret-password",
        api_key="super-secret-api-key",
    )


def _login_response() -> JsonResponse:
    return JsonResponse(
        status=200,
        headers={"CST": "secret-cst", "X-SECURITY-TOKEN": "secret-security-token"},
        payload={"currentAccountId": "ABC123"},
    )


def test_credentials_and_client_repr_do_not_expose_secrets() -> None:
    credentials = _credentials()
    client = IgDemoReadOnlyClient(credentials=credentials, transport=FakeTransport([]))

    rendered = f"{credentials!r} {client!r}"

    assert "demo-user" not in rendered
    assert "super-secret-password" not in rendered
    assert "super-secret-api-key" not in rendered


def test_read_only_client_exposes_only_none_false_execution_state() -> None:
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=FakeTransport([]))

    assert client.execution_capability == "NONE"
    assert client.order_execution_enabled is False
    for forbidden in ("order", "submit_order", "place_order", "deal", "cancel_order", "modify_order"):
        assert not hasattr(client, forbidden)


def test_login_accounts_market_prices_and_logout_use_read_only_routes() -> None:
    transport = FakeTransport(
        [
            _login_response(),
            JsonResponse(200, {}, {"accounts": [{"accountId": "ABC123"}]}),
            JsonResponse(200, {}, {"instrument": {"epic": "IX.D.DAX.IFMM.IP"}}),
            JsonResponse(200, {}, {"prices": [{"snapshotTimeUTC": "2026-09-14T08:00:00"}]}),
            JsonResponse(200, {}, {}),
        ]
    )
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=transport)

    client.login()
    accounts = client.accounts()
    market = client.market("IX.D.DAX.IFMM.IP")
    prices = client.m5_prices("IX.D.DAX.IFMM.IP", max_bars=40)
    client.logout()

    assert accounts["accounts"] == [{"accountId": "ABC123"}]
    assert market["instrument"] == {"epic": "IX.D.DAX.IFMM.IP"}
    assert prices["prices"] == [{"snapshotTimeUTC": "2026-09-14T08:00:00"}]
    assert client.authenticated is False
    assert [call["method"] for call in transport.calls] == ["POST", "GET", "GET", "GET", "DELETE"]
    assert [call["url"] for call in transport.calls] == [
        f"{IG_DEMO_BASE_URL}/session",
        f"{IG_DEMO_BASE_URL}/accounts",
        f"{IG_DEMO_BASE_URL}/markets/IX.D.DAX.IFMM.IP",
        f"{IG_DEMO_BASE_URL}/prices/IX.D.DAX.IFMM.IP",
        f"{IG_DEMO_BASE_URL}/session",
    ]
    assert transport.calls[3]["query"] == {"resolution": "MINUTE_5", "max": "40", "pageSize": "0"}
    assert transport.calls[0]["headers"]["VERSION"] == "2"
    assert transport.calls[1]["headers"]["VERSION"] == "1"
    assert transport.calls[2]["headers"]["VERSION"] == "3"
    assert transport.calls[3]["headers"]["VERSION"] == "3"
    assert transport.calls[4]["headers"]["VERSION"] == "1"


def test_authenticated_headers_are_bound_after_login() -> None:
    transport = FakeTransport(
        [
            _login_response(),
            JsonResponse(200, {}, {"accounts": []}),
        ]
    )
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=transport)

    client.login()
    client.accounts()

    headers = transport.calls[1]["headers"]
    assert headers["CST"] == "secret-cst"
    assert headers["X-SECURITY-TOKEN"] == "secret-security-token"
    assert headers["X-IG-API-KEY"] == "super-secret-api-key"


def test_login_context_is_hashed_and_reads_capture_server_clock_provenance() -> None:
    transport = FakeTransport([
        JsonResponse(
            200,
            {"CST": "secret-cst", "X-SECURITY-TOKEN": "secret-security-token"},
            {
                "currentAccountId": "ABC123",
                "accountType": "CFD",
                "currencyIsoCode": "EUR",
                "dealingEnabled": True,
                "timezoneOffset": 1,
            },
        ),
        JsonResponse(
            200,
            {"Date": "Tue, 15 Sep 2026 10:00:00 GMT", "X-REQUEST-ID": "private-id"},
            {"accounts": []},
        ),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    client.accounts()

    context = client.login_context
    assert context["currency"] == "EUR" and context["dealing_enabled"] is True
    assert len(context["account_context_fingerprint"]) == 64
    assert "ABC123" not in repr(context)
    observation = client.read_observations[0]
    assert observation.server_date_utc.isoformat() == "2026-09-15T10:00:00+00:00"
    assert len(observation.request_id_fingerprint) == 64
    assert "private-id" not in repr(observation)


def test_v4_market_and_bounded_activity_are_get_only() -> None:
    transport = FakeTransport([
        _login_response(),
        JsonResponse(200, {}, {"instrument": {}, "dealingRules": {}, "snapshot": {}}),
        JsonResponse(200, {}, {"activities": [], "metadata": {"paging": {}}}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    from datetime import datetime, timezone

    client.market_v4("IX.D.DAX.IFMM.IP")
    client.account_activity(
        from_utc=datetime(2026, 9, 8, tzinfo=timezone.utc),
        to_utc=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )
    assert [call["method"] for call in transport.calls] == ["POST", "GET", "GET"]
    assert transport.calls[1]["headers"]["VERSION"] == "4"
    assert transport.calls[2]["url"].endswith("/history/activity")
    assert transport.calls[2]["query"]["detailed"] == "true"


def test_unauthenticated_read_is_fail_closed() -> None:
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=FakeTransport([]))

    with pytest.raises(IgReadOnlyError, match="not authenticated"):
        client.accounts()


def test_failed_login_reports_only_normalized_error_code() -> None:
    transport = FakeTransport(
        [
            JsonResponse(
                401,
                {},
                {
                    "errorCode": "error.security.invalid-details",
                    "password": "must-never-appear",
                },
            )
        ]
    )
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=transport)

    with pytest.raises(IgReadOnlyError) as exc_info:
        client.login()

    message = str(exc_info.value)
    assert "HTTP 401" in message
    assert "error.security.invalid-details" in message
    assert "must-never-appear" not in message
    assert "super-secret-password" not in message


def test_login_requires_both_session_tokens() -> None:
    client = IgDemoReadOnlyClient(
        credentials=_credentials(),
        transport=FakeTransport([JsonResponse(200, {"CST": "only-cst"}, {})]),
    )

    with pytest.raises(IgReadOnlyError, match="X-SECURITY-TOKEN"):
        client.login()


def test_client_is_hard_pinned_to_demo_endpoint() -> None:
    with pytest.raises(ValueError, match="pinned to the Demo API"):
        IgDemoReadOnlyClient(
            credentials=_credentials(),
            transport=FakeTransport([]),
            base_url="https://api.ig.com/gateway/deal",
        )


def test_epic_and_bar_limit_validation_fail_closed_before_transport() -> None:
    transport = FakeTransport([_login_response()])
    client = IgDemoReadOnlyClient(credentials=_credentials(), transport=transport)
    client.login()

    with pytest.raises(ValueError, match="invalid path"):
        client.market("IX.D.DAX.IFMM.IP?bad=1")
    with pytest.raises(ValueError, match="between 1 and 1000"):
        client.m5_prices("IX.D.DAX.IFMM.IP", max_bars=0)

    assert len(transport.calls) == 1


@pytest.mark.parametrize("pages", [2, 10, True, "1", None])
def test_unpaged_request_does_not_accept_remaining_or_invalid_pagination(pages) -> None:
    transport = FakeTransport([_login_response(), JsonResponse(
        200, {}, {"prices": [], "metadata": {"pageData": {"totalPages": pages}}},
    )])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    with pytest.raises(IgReadOnlyError, match="remains paginated"):
        client.m5_prices("IX.D.DAX.IFMM.IP")
    assert transport.calls[-1]["query"]["pageSize"] == "0"


@pytest.mark.parametrize("secret", ["Bearer SYNTHETIC_SENTINEL", "postgres://user:secret@host/db",
                                    "error.security.SYNTHETIC_SENTINEL"])
def test_unrecognized_provider_error_code_is_not_echoed(secret) -> None:
    transport = FakeTransport([JsonResponse(401, {}, {"errorCode": secret})])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    with pytest.raises(IgReadOnlyError) as error:
        client.login()
    assert secret not in str(error.value)
    assert "SYNTHETIC_SENTINEL" not in str(error.value)
    assert "HTTP 401" in str(error.value)


def test_logout_transport_failure_discards_local_tokens_without_retry():
    calls = []
    class Transport:
        def request(self, **kwargs):
            calls.append(kwargs["method"])
            if kwargs["method"] == "POST":
                return _login_response()
            raise IgReadOnlyError("IG read-only transport unavailable")
    client = IgDemoReadOnlyClient(_credentials(), transport=Transport())
    client.login()
    with pytest.raises(IgReadOnlyError):
        client.logout()
    assert client.authenticated is False
    client.logout()  # No retained token: no second remote cleanup attempt.
    assert calls == ["POST", "DELETE"]


def test_same_session_repeated_price_get_failure_does_not_relogin():
    transport = FakeTransport([
        _login_response(),
        JsonResponse(200, {}, {"prices": []}),
        JsonResponse(401, {}, {"errorCode": "error.security.client-token-invalid"}),
        JsonResponse(200, {}, {}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport=transport)
    client.login()
    client.m5_prices("IX.D.DAX.IFMM.IP")
    with pytest.raises(IgReadOnlyError, match="HTTP 401"):
        client.m5_prices("IX.D.DAX.IFMM.IP")
    client.logout()
    assert not client.authenticated
    assert [call["method"] for call in transport.calls] == ["POST", "GET", "GET", "DELETE"]
    assert transport.calls[1]["headers"]["CST"] == transport.calls[2]["headers"]["CST"]


def test_readiness_resource_contracts_use_official_versions_paths_and_shapes() -> None:
    transport = FakeTransport([
        _login_response(),
        JsonResponse(200, {}, {"accounts": []}),
        JsonResponse(200, {}, {"positions": []}),
        JsonResponse(200, {}, {"workingOrders": []}),
        JsonResponse(200, {}, {"instrument": {}, "dealingRules": {}, "snapshot": {}}),
        JsonResponse(200, {}, {"activities": [], "metadata": {"paging": {}}}),
        JsonResponse(200, {}, {"prices": [], "metadata": {"pageData": {"totalPages": 1}}}),
        JsonResponse(200, {}, {"positions": []}),
        JsonResponse(200, {}, {"workingOrders": []}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    from datetime import datetime, timedelta, timezone
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    results = [
        client.readiness_accounts(),
        client.readiness_positions("POSITIONS_A"),
        client.readiness_working_orders("WORKING_ORDERS_A"),
        client.readiness_market_v4("IX.D.DAX.IFMM.IP"),
        client.readiness_account_activity(from_utc=now - timedelta(days=7), to_utc=now),
        client.readiness_m5_prices("IX.D.DAX.IFMM.IP"),
        client.readiness_positions("POSITIONS_B"),
        client.readiness_working_orders("WORKING_ORDERS_B"),
    ]
    assert [item.status for item in results] == ["PASS"] * 8
    assert [call["url"].removeprefix(IG_DEMO_BASE_URL) for call in transport.calls[1:]] == [
        "/accounts", "/positions", "/working-orders", "/markets/IX.D.DAX.IFMM.IP",
        "/history/activity", "/prices/IX.D.DAX.IFMM.IP", "/positions", "/working-orders",
    ]
    assert [call["headers"]["VERSION"] for call in transport.calls[1:]] == [
        "1", "2", "2", "4", "3", "3", "2", "2",
    ]
    assert all(call["method"] == "GET" for call in transport.calls[1:])


def test_readiness_http_failure_does_not_hide_independent_reads() -> None:
    transport = FakeTransport([
        _login_response(),
        JsonResponse(500, {"X-REQUEST-ID": "private-request"}, {"errorCode": "system.error"}),
        JsonResponse(200, {}, {"positions": []}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    failed = client.readiness_accounts()
    passed = client.readiness_positions("POSITIONS_A")
    assert failed.status == "FAIL"
    assert failed.reason_code == "IG_READ_ACCOUNTS_HTTP_FAILED"
    assert failed.http_status_class == "HTTP_5XX"
    assert failed.provider_error_code == "system.error"
    assert failed.request_id_fingerprint and "private-request" not in repr(failed.safe_view())
    assert passed.status == "PASS"
    assert [call["method"] for call in transport.calls] == ["POST", "GET", "GET"]


def test_readiness_401_blocks_later_reads_without_relogin_or_get() -> None:
    transport = FakeTransport([
        _login_response(),
        JsonResponse(401, {}, {"errorCode": "error.security.client-token-invalid"}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    failed = client.readiness_accounts()
    blocked = client.readiness_positions("POSITIONS_A")
    assert failed.status == "FAIL" and failed.http_status_class == "HTTP_4XX"
    assert blocked.status == "BLOCKED"
    assert blocked.reason_code == "IG_READ_AUTH_PRECONDITION_BLOCKED"
    assert blocked.request_started_at is None
    assert [call["method"] for call in transport.calls] == ["POST", "GET"]


def test_readiness_shape_failure_is_sanitized_and_next_read_continues() -> None:
    transport = FakeTransport([
        _login_response(), JsonResponse(200, {}, {"accounts": "wrong"}),
        JsonResponse(200, {}, {"positions": []}),
    ])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    invalid = client.readiness_accounts()
    following = client.readiness_positions("POSITIONS_A")
    assert invalid.status == "FAIL"
    assert invalid.response_shape_status == "INVALID"
    assert invalid.reason_code == "IG_READ_ACCOUNTS_RESPONSE_SHAPE_INVALID"
    assert following.status == "PASS"


def test_readiness_transport_unknown_is_not_retried_and_next_read_continues() -> None:
    class Transport:
        calls = 0
        def request(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return _login_response()
            if self.calls == 2:
                raise OSError("secret transport detail")
            return JsonResponse(200, {}, {"positions": []})
    transport = Transport()
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    unknown = client.readiness_accounts()
    passed = client.readiness_positions("POSITIONS_A")
    assert unknown.status == "UNKNOWN"
    assert unknown.reason_code == "IG_READ_ACCOUNTS_TRANSPORT_UNKNOWN"
    assert "secret" not in repr(unknown.safe_view())
    assert passed.status == "PASS"
    assert transport.calls == 3


@pytest.mark.parametrize(
    ("resource", "payload", "invoke"),
    [
        ("ACCOUNTS", {"accounts": {}}, lambda client, now: client.readiness_accounts()),
        ("POSITIONS_A", {"positions": {}}, lambda client, now: client.readiness_positions("POSITIONS_A")),
        ("WORKING_ORDERS_A", {"workingOrders": {}}, lambda client, now: client.readiness_working_orders("WORKING_ORDERS_A")),
        ("MARKET_V4", {"instrument": {}, "snapshot": {}}, lambda client, now: client.readiness_market_v4("IX.D.DAX.IFMM.IP")),
        ("ACTIVITY_HISTORY", {"activities": [], "metadata": []}, lambda client, now: client.readiness_account_activity(from_utc=now - timedelta(days=7), to_utc=now)),
        ("M5_PRICES", {"prices": [], "metadata": {"pageData": {"totalPages": 2}}}, lambda client, now: client.readiness_m5_prices("IX.D.DAX.IFMM.IP")),
        ("POSITIONS_B", {"positions": None}, lambda client, now: client.readiness_positions("POSITIONS_B")),
        ("WORKING_ORDERS_B", {"workingOrders": None}, lambda client, now: client.readiness_working_orders("WORKING_ORDERS_B")),
    ],
)
def test_each_readiness_resource_has_a_fixed_shape_failure(
    resource, payload, invoke
) -> None:
    transport = FakeTransport([_login_response(), JsonResponse(200, {}, payload)])
    client = IgDemoReadOnlyClient(_credentials(), transport)
    client.login()
    result = invoke(client, datetime(2026, 9, 15, tzinfo=timezone.utc))
    assert result.resource == resource
    assert result.status == "FAIL"
    assert result.reason_code == f"IG_READ_{resource}_RESPONSE_SHAPE_INVALID"
    assert result.response_shape_status == "INVALID"
    assert len(transport.calls) == 2
