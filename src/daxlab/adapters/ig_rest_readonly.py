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
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
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


@dataclass(frozen=True, slots=True)
class IgReadObservation:
    """Credential-free timing/provenance for one completed read."""

    resource: str
    request_started_at: datetime
    response_observed_at: datetime
    server_date_utc: datetime | None
    request_id_fingerprint: str | None

    def __post_init__(self) -> None:
        for value in (self.request_started_at, self.response_observed_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("IG read observation timestamps must be timezone-aware")
        if self.response_observed_at < self.request_started_at:
            raise ValueError("IG read observation clock moved backwards")
        if self.server_date_utc is not None and (
            self.server_date_utc.tzinfo is None
            or self.server_date_utc.utcoffset() is None
        ):
            raise ValueError("IG server date must be timezone-aware")


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
    _account_context_fingerprint: str | None = field(default=None, init=False, repr=False)
    _login_context: dict[str, object] = field(default_factory=dict, init=False, repr=False)
    _read_observations: list[IgReadObservation] = field(default_factory=list, init=False, repr=False)

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

    @property
    def login_context(self) -> Mapping[str, object]:
        """Redacted context captured from the single login response."""
        if not self.authenticated or self._account_context_fingerprint is None:
            raise IgReadOnlyError("IG authenticated account context unavailable")
        return dict(self._login_context)

    @property
    def read_observations(self) -> tuple[IgReadObservation, ...]:
        return tuple(self._read_observations)

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
            self._capture_login_context(response.payload)
            self._session_state = "AUTHENTICATED"
        except Exception:
            self._session_state = "QUERY_REQUIRED"
            raise

    def _request(self, **kwargs) -> JsonResponse:
        url, method = kwargs.get("url"), kwargs.get("method")
        if (self.base_url != IG_DEMO_BASE_URL or not isinstance(url, str)
                or not url.startswith(IG_DEMO_BASE_URL + "/")
                or method not in ("GET", "POST", "DELETE")
                or (method != "GET" and url != IG_DEMO_BASE_URL + "/session")):
            raise IgReadOnlyError("IG hard DEMO/read-only transport boundary blocked")
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

    def market_v4(self, epic: str) -> Mapping[str, object]:
        """Read v4 market metadata, including epoch quote time when supplied."""
        clean_epic = _clean_epic(epic)
        return self._get_json(f"/markets/{clean_epic}", version="4")

    def account_activity(
        self, *, from_utc: datetime, to_utc: datetime, page_size: int = 500
    ) -> Mapping[str, object]:
        """Read bounded account activity; never follows an unknown paging link."""
        for value, name in ((from_utc, "from_utc"), (to_utc, "to_utc")):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if to_utc <= from_utc:
            raise ValueError("account activity interval must be positive")
        if type(page_size) is not int or not 1 <= page_size <= 500:
            raise ValueError("page_size must be between 1 and 500")
        payload = self._get_json(
            "/history/activity",
            version="3",
            query={
                "from": from_utc.astimezone(timezone.utc).isoformat(),
                "to": to_utc.astimezone(timezone.utc).isoformat(),
                "detailed": "true",
                "pageSize": str(page_size),
            },
        )
        return payload

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
        started = datetime.now(timezone.utc)
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
        observed = datetime.now(timezone.utc)
        self._read_observations.append(
            IgReadObservation(
                resource=path,
                request_started_at=started,
                response_observed_at=observed,
                server_date_utc=_http_date_or_none(response.headers),
                request_id_fingerprint=_header_fingerprint_or_none(
                    response.headers, "X-REQUEST-ID"
                ),
            )
        )
        self._read_count += 1
        return response.payload

    def _capture_login_context(self, payload: object) -> None:
        if not isinstance(payload, Mapping):
            raise IgReadOnlyError("IG login response must be a JSON object")
        account_id = payload.get("currentAccountId") or payload.get("accountId")
        context = {
            "environment": "IG_DEMO",
            "account_type": _safe_token(payload.get("accountType")),
            "currency": _safe_token(payload.get("currencyIsoCode")),
            "dealing_enabled": payload.get("dealingEnabled")
            if isinstance(payload.get("dealingEnabled"), bool)
            else None,
            "timezone_offset_hours": _finite_number_or_none(payload.get("timezoneOffset")),
        }
        if isinstance(account_id, str) and account_id:
            identity = json.dumps(
                {"environment": "IG_DEMO", "active_account_id": account_id},
                sort_keys=True,
                separators=(",", ":"),
            )
            self._account_context_fingerprint = sha256(identity.encode()).hexdigest()
            context["account_context_fingerprint"] = self._account_context_fingerprint
        self._login_context = context

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


def _safe_token(value: object) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    return value if len(value) <= 32 and value.replace("_", "").isalnum() else None


def _finite_number_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if isfinite(result) else None


def _http_date_or_none(headers: Mapping[str, str]) -> datetime | None:
    try:
        raw = next(
            value
            for key, value in headers.items()
            if key.casefold() == "date" and isinstance(value, str)
        )
        parsed = parsedate_to_datetime(raw)
    except (StopIteration, TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _header_fingerprint_or_none(
    headers: Mapping[str, str], name: str
) -> str | None:
    for key, value in headers.items():
        if key.casefold() == name.casefold() and isinstance(value, str) and value:
            return sha256(value.encode()).hexdigest()
    return None
