"""Minimal fail-closed IG Demo REST client with no dealing capability.

This adapter intentionally exposes only read operations needed by the SHADOW
broker lane: session authentication, account/position/working-order inventory,
market detail, M5 price history and session logout. It has no order/position
mutation method and hard reports ``execution_capability=NONE`` /
``order_execution_enabled=False``.

The default transport uses only the Python standard library. Tests can inject a
transport without network access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from math import isfinite
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


IG_DEMO_BASE_URL = "https://demo-api.ig.com/gateway/deal"
EXECUTION_CAPABILITY = "NONE"
ORDER_EXECUTION_ENABLED = False
_SAFE_ERROR_CODES = frozenset({
    "error.security.invalid-details", "error.security.api-key-invalid",
    "error.security.api-key-disabled", "error.security.account-token-invalid",
    "error.security.client-token-invalid", "error.public-api.exceeded-account-allowance",
    "error.public-api.exceeded-api-key-allowance",
    "error.public-api.exceeded-account-historical-data-allowance",
    "error.invalid.daterange", "error.malformed.date", "invalid.input", "system.error",
})


class IgReadOnlyError(RuntimeError):
    """Normalized IG read-only transport/API failure without secret payloads."""


@dataclass(frozen=True, slots=True)
class IgDemoCredentials:
    identifier: str = field(repr=False)
    password: str = field(repr=False)
    api_key: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in ("identifier", "password", "api_key"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required")


@dataclass(frozen=True, slots=True)
class IgSessionTokens:
    cst: str = field(repr=False)
    security_token: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.cst or not self.security_token:
            raise ValueError("IG session requires CST and X-SECURITY-TOKEN")


@dataclass(frozen=True, slots=True)
class JsonResponse:
    status: int
    headers: Mapping[str, str]
    payload: object


class JsonTransport(Protocol):
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | None = None,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 20.0,
    ) -> JsonResponse: ...


@dataclass(frozen=True, slots=True)
class UrllibJsonTransport:
    """Small JSON transport using stdlib only; never logs headers or bodies."""

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
        if query:
            url = f"{url}?{urlencode(query)}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(url=url, data=data, headers=dict(headers), method=method)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
                return JsonResponse(
                    status=int(response.status),
                    headers={key: value for key, value in response.headers.items()},
                    payload=payload,
                )
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {}
            return JsonResponse(
                status=int(exc.code),
                headers={key: value for key, value in exc.headers.items()},
                payload=payload,
            )
        except URLError:
            raise IgReadOnlyError("IG read-only transport unavailable") from None
        except (json.JSONDecodeError, UnicodeError):
            raise IgReadOnlyError("IG read-only response contains malformed JSON") from None


@dataclass(slots=True)
class IgDemoReadOnlyClient:
    credentials: IgDemoCredentials = field(repr=False)
    transport: JsonTransport = field(default_factory=UrllibJsonTransport, repr=False)
    base_url: str = IG_DEMO_BASE_URL
    timeout_seconds: float = 20.0
    _tokens: IgSessionTokens | None = field(default=None, init=False, repr=False)
    _session_state: str = field(default="NEW", init=False)
    _read_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.base_url != IG_DEMO_BASE_URL:
            raise ValueError("IG read-only client is pinned to the Demo API endpoint")
        if (type(self.timeout_seconds) not in (int, float)
                or not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0):
            raise ValueError("timeout_seconds must be positive")

    @property
    def execution_capability(self) -> str:
        return EXECUTION_CAPABILITY

    @property
    def order_execution_enabled(self) -> bool:
        return ORDER_EXECUTION_ENABLED

    @property
    def authenticated(self) -> bool:
        return self._tokens is not None and self._session_state == "AUTHENTICATED"

    @property
    def session_health(self) -> dict[str, object]:
        """Credential-free local lifecycle; authentication is not broker truth."""
        return {"state": self._session_state, "authenticated": self.authenticated,
                "successful_reads": self._read_count, "feed_freshness": "UNKNOWN",
                "inventory_truth": "UNKNOWN", "automatic_relogin": False,
                "execution_capability": EXECUTION_CAPABILITY,
                "order_execution_enabled": ORDER_EXECUTION_ENABLED}

    def login(self) -> None:
        if self._session_state != "NEW":
            raise IgReadOnlyError("IG session owner already consumed; no relogin")
        self._session_state = "LOGIN_PENDING"
        try:
            response = self._request(
                method="POST", url=f"{self.base_url}/session",
                headers=self._base_headers(version="2"),
                body={"identifier": self.credentials.identifier,
                      "password": self.credentials.password, "encryptedPassword": False},
                timeout_seconds=self.timeout_seconds,
            )
            self._require_success(response, action="session login")
            cst = _header(response.headers, "CST")
            security_token = _header(response.headers, "X-SECURITY-TOKEN")
            self._tokens = IgSessionTokens(cst=cst, security_token=security_token)
            self._session_state = "AUTHENTICATED"
        except Exception:
            self._session_state = "QUERY_REQUIRED"
            raise

    def _request(self, **kwargs) -> JsonResponse:
        try:
            response = self.transport.request(**kwargs)
        except Exception:
            raise IgReadOnlyError("IG read-only transport outcome unknown; no retry") from None
        if (not isinstance(response, JsonResponse) or type(response.status) is not int
                or not isinstance(response.headers, Mapping)):
            raise IgReadOnlyError("IG read-only transport returned malformed response")
        return response

    def accounts(self) -> Mapping[str, object]:
        return self._get_json("/accounts", version="1")

    def positions(self) -> Mapping[str, object]:
        return self._get_json("/positions", version="2")

    def working_orders(self) -> Mapping[str, object]:
        return self._get_json("/workingorders", version="2")

    def market(self, epic: str) -> Mapping[str, object]:
        clean_epic = _clean_epic(epic)
        return self._get_json(f"/markets/{clean_epic}", version="3")

    def m5_prices(self, epic: str, *, max_bars: int = 40) -> Mapping[str, object]:
        clean_epic = _clean_epic(epic)
        if isinstance(max_bars, bool) or not isinstance(max_bars, int) or not 1 <= max_bars <= 1000:
            raise ValueError("max_bars must be an integer between 1 and 1000")
        payload = self._get_json(
            f"/prices/{clean_epic}",
            version="3",
            # IG v3 defaults to pageSize=20. With max=40 the first page alone
            # may contain older history, causing a false stale-feed diagnosis.
            query={"resolution": "MINUTE_5", "max": str(max_bars), "pageSize": "0"},
        )
        metadata = payload.get("metadata")
        if isinstance(metadata, Mapping) and isinstance(metadata.get("pageData"), Mapping):
            pages = metadata["pageData"].get("totalPages")
            if isinstance(pages, bool) or not isinstance(pages, int) or pages not in (0, 1):
                self._session_state = "QUERY_REQUIRED"
                raise IgReadOnlyError("IG M5 history response remains paginated")
        return payload

    def logout(self) -> None:
        if self._tokens is None:
            self._session_state = "CLOSED"
            return
        try:
            response = self._request(
                method="DELETE",
                url=f"{self.base_url}/session",
                headers=self._auth_headers(version="1"),
                timeout_seconds=self.timeout_seconds,
            )
            self._require_success(response, action="session logout")
        finally:
            self._tokens = None
            self._session_state = "CLOSED"

    def _get_json(
        self,
        path: str,
        *,
        version: str,
        query: Mapping[str, str] | None = None,
    ) -> Mapping[str, object]:
        if self._session_state != "AUTHENTICATED":
            raise IgReadOnlyError("IG read-only client is not authenticated; session query required")
        try:
            response = self._request(
                method="GET", url=f"{self.base_url}{path}",
                headers=self._auth_headers(version=version), query=query,
                timeout_seconds=self.timeout_seconds,
            )
            self._require_success(response, action=f"GET {path}")
            if not isinstance(response.payload, Mapping):
                raise IgReadOnlyError("IG read-only response must be a JSON object")
        except Exception:
            self._session_state = "QUERY_REQUIRED"
            raise
        self._read_count += 1
        return response.payload

    def _base_headers(self, *, version: str) -> dict[str, str]:
        return {
            "X-IG-API-KEY": self.credentials.api_key,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
            "VERSION": version,
        }

    def _auth_headers(self, *, version: str) -> dict[str, str]:
        if self._tokens is None:
            raise IgReadOnlyError("IG read-only client is not authenticated")
        headers = self._base_headers(version=version)
        headers["CST"] = self._tokens.cst
        headers["X-SECURITY-TOKEN"] = self._tokens.security_token
        return headers

    @staticmethod
    def _require_success(response: JsonResponse, *, action: str) -> None:
        if 200 <= response.status < 300:
            return
        error_code = None
        if isinstance(response.payload, Mapping):
            candidate = response.payload.get("errorCode")
            if isinstance(candidate, str) and candidate in _SAFE_ERROR_CODES:
                error_code = candidate
        suffix = "" if error_code is None else f" ({error_code})"
        raise IgReadOnlyError(f"IG read-only {action} failed: HTTP {response.status}{suffix}")


def _header(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if isinstance(key, str) and key.casefold() == name.casefold() and isinstance(value, str) and value:
            return value
    raise IgReadOnlyError(f"IG session response missing required {name} header")


def _clean_epic(epic: str) -> str:
    if not isinstance(epic, str) or not epic or epic.strip() != epic:
        raise ValueError("epic must be non-empty without surrounding whitespace")
    if any(character in epic for character in ("/", "?", "#")):
        raise ValueError("epic contains invalid path characters")
    return epic
