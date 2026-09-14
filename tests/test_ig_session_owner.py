from __future__ import annotations

from math import inf, nan

import pytest

from daxlab.adapters.ig_rest_readonly import (
    IgDemoCredentials, IgDemoReadOnlyClient, IgReadOnlyError, JsonResponse,
)


class Transport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs["method"])
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def login_response():
    return JsonResponse(200, {"CST": "secret-cst", "X-SECURITY-TOKEN": "secret-token"}, {})


def client(transport):
    return IgDemoReadOnlyClient(IgDemoCredentials("identifier", "password", "api-key"), transport)


def test_one_owner_consumes_login_once_including_after_logout():
    transport = Transport([login_response(), JsonResponse(200, {}, {})])
    owner = client(transport)
    owner.login()
    with pytest.raises(IgReadOnlyError, match="no relogin"):
        owner.login()
    owner.logout()
    with pytest.raises(IgReadOnlyError, match="no relogin"):
        owner.login()
    assert transport.calls == ["POST", "DELETE"]


@pytest.mark.parametrize("failure", [
    JsonResponse(401, {}, {"errorCode": "error.security.client-token-invalid"}),
    JsonResponse(429, {}, {}), JsonResponse(503, {}, {}),
    JsonResponse(200, {}, None), JsonResponse(200, {}, []),
    None, {}, JsonResponse(True, {}, {}),
    TimeoutError("password-secret"), RuntimeError("password-secret"),
])
def test_any_read_failure_latches_query_required_and_allows_one_cleanup(failure):
    transport = Transport([login_response(), failure, JsonResponse(200, {}, {})])
    owner = client(transport)
    owner.login()
    with pytest.raises(IgReadOnlyError) as error:
        owner.accounts()
    assert "password-secret" not in str(error.value)
    assert owner.session_health["state"] == "QUERY_REQUIRED"
    assert not owner.authenticated
    for read in (owner.accounts, owner.positions, owner.working_orders):
        with pytest.raises(IgReadOnlyError):
            read()
    with pytest.raises(IgReadOnlyError):
        owner.login()
    owner.logout()
    owner.logout()
    assert transport.calls == ["POST", "GET", "DELETE"]
    assert owner.session_health["state"] == "CLOSED"


@pytest.mark.parametrize("failure", [
    JsonResponse(401, {}, {}), JsonResponse(200, {"CST": "one-token"}, {}),
    TimeoutError("password-secret"), None,
])
def test_failed_or_unknown_login_cannot_replay(failure):
    transport = Transport([failure])
    owner = client(transport)
    with pytest.raises(IgReadOnlyError):
        owner.login()
    with pytest.raises(IgReadOnlyError):
        owner.login()
    owner.logout()
    assert transport.calls == ["POST"]


def test_health_does_not_claim_feed_or_inventory_and_contains_no_credentials():
    transport = Transport([login_response(), JsonResponse(200, {}, {"accounts": []})])
    owner = client(transport)
    assert owner.session_health["state"] == "NEW"
    owner.login()
    owner.accounts()
    health = owner.session_health
    assert health["successful_reads"] == 1
    assert health["feed_freshness"] == health["inventory_truth"] == "UNKNOWN"
    assert health["execution_capability"] == "NONE"
    assert health["order_execution_enabled"] is False
    assert "secret" not in str(health)
    assert "password" not in str(health)


@pytest.mark.parametrize("timeout", [nan, inf, -inf, 0, -1, True, "20"])
def test_timeout_must_be_finite_numeric_positive(timeout):
    with pytest.raises(ValueError):
        IgDemoReadOnlyClient(IgDemoCredentials("i", "p", "k"), timeout_seconds=timeout)


def test_remaining_pagination_also_latches_read_owner():
    transport = Transport([login_response(), JsonResponse(
        200, {}, {"prices": [], "metadata": {"pageData": {"totalPages": 2}}},
    ), JsonResponse(200, {}, {})])
    owner = client(transport)
    owner.login()
    with pytest.raises(IgReadOnlyError):
        owner.m5_prices("IX.D.DAX.IFMM.IP")
    with pytest.raises(IgReadOnlyError):
        owner.positions()
    owner.logout()
    assert transport.calls == ["POST", "GET", "DELETE"]
