from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from daxlab.adapters.ig_rest_readonly import (
    IG_DEMO_BASE_URL,
    IgDemoCredentials,
    IgDemoReadOnlyClient,
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
                "body": body,
                "query": query,
            }
        )
        return self.responses.pop(0)


def test_positions_and_working_orders_are_get_only_v2_inventory_reads() -> None:
    transport = FakeTransport(
        [
            JsonResponse(
                200,
                {"CST": "cst", "X-SECURITY-TOKEN": "security"},
                {},
            ),
            JsonResponse(200, {}, {"positions": []}),
            JsonResponse(200, {}, {"workingOrders": []}),
        ]
    )
    client = IgDemoReadOnlyClient(
        credentials=IgDemoCredentials("demo", "password", "api-key"),
        transport=transport,
    )

    client.login()
    positions = client.positions()
    working_orders = client.working_orders()

    assert positions == {"positions": []}
    assert working_orders == {"workingOrders": []}
    assert [call["method"] for call in transport.calls] == ["POST", "GET", "GET"]
    assert transport.calls[1]["url"] == f"{IG_DEMO_BASE_URL}/positions"
    assert transport.calls[2]["url"] == f"{IG_DEMO_BASE_URL}/working-orders"
    assert transport.calls[1]["headers"]["VERSION"] == "2"
    assert transport.calls[2]["headers"]["VERSION"] == "2"
    assert transport.calls[1]["body"] is None
    assert transport.calls[2]["body"] is None
    assert client.execution_capability == "NONE"
    assert client.order_execution_enabled is False
