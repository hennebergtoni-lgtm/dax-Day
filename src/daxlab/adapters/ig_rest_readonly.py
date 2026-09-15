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
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
from math import isfinite
from typing import Callable, Mapping, Protocol
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
    "error.security.account-token-missing", "error.security.client-token-missing",
    "error.security.oauth-token-invalid", "error.security.api-key-missing",
    "endpoint.unavailable.for.api-key", "error.public-api.epic-not-found",
    "error.trading.otc.instrument-not-found", "invalid.url",
    "error.request.invalid.date-range", "error.request.invalid.page-size",
    "error.security.api-key-restricted", "error.security.api-key-revoked",
    "error.public-api.exceeded-account-trading-allowance",
    "error.public-api.failure.encryption.required",
    "error.public-api.failure.kyc.required",
    "error.public-api.failure.missing.credentials",
    "error.public-api.failure.pending.agreements.required",
    "error.public-api.failure.preferred.account.disabled",
    "error.public-api.failure.preferred.account.not.set",
    "error.public-api.failure.product-code-not-allowed",
    "error.public-api.failure.stockbroking-not-supported",
})
_SESSION_INVALID_ERROR_CODES = frozenset({
    "error.security.account-token-invalid",
    "error.security.account-token-missing",
    "error.security.client-token-invalid",
    "error.security.client-token-missing",
    "error.security.oauth-token-invalid",
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


@dataclass(frozen=True, slots=True)
class IgReadinessRead:
    """One sanitized Step2238 GET outcome plus an in-memory successful payload."""

    resource: str
    endpoint_family: str
    status: str
    reason_code: str
    response_shape_status: str
    request_started_at: datetime | None
    response_observed_at: datetime | None
    http_status_class: str | None
    provider_error_code: str | None
    request_id_fingerprint: str | None
    server_date_utc: datetime | None
    payload: Mapping[str, object] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "FAIL", "BLOCKED", "UNKNOWN"}:
            raise ValueError("invalid IG readiness status")
        if self.provider_error_code is not None and self.provider_error_code not in _SAFE_ERROR_CODES:
            raise ValueError("unsafe IG provider error code")
        if self.http_status_class not in {
            None, "HTTP_1XX", "HTTP_2XX", "HTTP_3XX", "HTTP_4XX", "HTTP_5XX", "HTTP_OTHER"
        }:
            raise ValueError("invalid IG HTTP status class")
        if self.request_id_fingerprint is not None and (
            len(self.request_id_fingerprint) != 64
            or any(value not in "0123456789abcdef" for value in self.request_id_fingerprint)
        ):
            raise ValueError("invalid IG request fingerprint")
        for value in (self.request_started_at, self.response_observed_at, self.server_date_utc):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("IG readiness timestamps must be timezone-aware")
        if (self.request_started_at is not None and self.response_observed_at is not None
                and self.response_observed_at < self.request_started_at):
            raise ValueError("IG readiness observation clock moved backwards")

    def safe_view(self) -> dict[str, object]:
        return {
            "resource": self.resource,
            "endpoint_family": self.endpoint_family,
            "status": self.status,
            "reason_code": self.reason_code,
            "http_status_class": self.http_status_class,
            "provider_error_code": self.provider_error_code,
            "response_shape_status": self.response_shape_status,
            "request_started_at_utc": None if self.request_started_at is None else self.request_started_at.isoformat(),
            "response_observed_at_utc": None if self.response_observed_at is None else self.response_observed_at.isoformat(),
            "request_id_fingerprint": self.request_id_fingerprint,
            "server_date_utc": None if self.server_date_utc is None else self.server_date_utc.isoformat(),
        }


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
        payload = self._get_json(
            "/history/activity",
            version="3",
            query=_activity_query(from_utc, to_utc, page_size),
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

    def readiness_accounts(self) -> IgReadinessRead:
        return self._readiness_get(
            resource="ACCOUNTS", endpoint_family="ACCOUNTS_V1", path="/accounts",
            version="1", shape=_shape_accounts,
        )

    def readiness_positions(self, resource: str) -> IgReadinessRead:
        if resource not in {"POSITIONS_A", "POSITIONS_B"}:
            raise ValueError("invalid readiness positions resource")
        return self._readiness_get(
            resource=resource, endpoint_family="POSITIONS_V2", path="/positions",
            version="2", shape=_shape_positions,
        )

    def readiness_working_orders(self, resource: str) -> IgReadinessRead:
        if resource not in {"WORKING_ORDERS_A", "WORKING_ORDERS_B"}:
            raise ValueError("invalid readiness working-orders resource")
        return self._readiness_get(
            resource=resource, endpoint_family="WORKING_ORDERS_V2",
            path="/workingorders", version="2", shape=_shape_working_orders,
        )

    def readiness_market_v4(self, epic: str) -> IgReadinessRead:
        clean_epic = _clean_epic(epic)
        return self._readiness_get(
            resource="MARKET_V4", endpoint_family="MARKET_V4",
            path=f"/markets/{clean_epic}", version="4", shape=_shape_market_v4,
        )

    def readiness_account_activity(
        self, *, from_utc: datetime, to_utc: datetime, page_size: int = 500
    ) -> IgReadinessRead:
        return self._readiness_get(
            resource="ACTIVITY_HISTORY", endpoint_family="ACTIVITY_HISTORY_V3",
            path="/history/activity", version="3", shape=_shape_activity,
            query=_activity_query(from_utc, to_utc, page_size),
        )

    def readiness_m5_prices(self, epic: str, *, max_bars: int = 40) -> IgReadinessRead:
        clean_epic = _clean_epic(epic)
        if isinstance(max_bars, bool) or not isinstance(max_bars, int) or not 1 <= max_bars <= 1000:
            raise ValueError("max_bars must be an integer between 1 and 1000")
        return self._readiness_get(
            resource="M5_PRICES", endpoint_family="PRICES_V3",
            path=f"/prices/{clean_epic}", version="3", shape=_shape_prices,
            query={"resolution": "MINUTE_5", "max": str(max_bars), "pageSize": "0"},
        )

    def _readiness_get(
        self,
        *,
        resource: str,
        endpoint_family: str,
        path: str,
        version: str,
        shape: Callable[[Mapping[str, object]], bool],
        query: Mapping[str, str] | None = None,
    ) -> IgReadinessRead:
        """Execute one GET without retry; known independent failures stay observable."""
        if self._session_state != "AUTHENTICATED":
            return IgReadinessRead(
                resource, endpoint_family, "BLOCKED", "IG_READ_AUTH_PRECONDITION_BLOCKED",
                "NOT_EVALUATED", None, None, None, None, None, None,
            )
        started = datetime.now(timezone.utc)
        try:
            response = self._request(
                method="GET", url=f"{self.base_url}{path}",
                headers=self._auth_headers(version=version), query=query,
                timeout_seconds=self.timeout_seconds,
            )
        except Exception:
            observed = datetime.now(timezone.utc)
            return IgReadinessRead(
                resource, endpoint_family, "UNKNOWN",
                f"IG_READ_{resource}_TRANSPORT_UNKNOWN", "NOT_OBSERVED",
                started, observed, None, None, None, None,
            )
        observed = datetime.now(timezone.utc)
        status_class = _http_status_class(response.status)
        provider_code = _safe_provider_error(response.payload)
        request_fingerprint = _header_fingerprint_or_none(response.headers, "X-REQUEST-ID")
        server_date = _http_date_or_none(response.headers)
        if not 200 <= response.status < 300:
            if response.status == 401 or provider_code in _SESSION_INVALID_ERROR_CODES:
                self._session_state = "QUERY_REQUIRED"
            return IgReadinessRead(
                resource, endpoint_family, "FAIL", f"IG_READ_{resource}_HTTP_FAILED",
                "NOT_EVALUATED", started, observed, status_class, provider_code,
                request_fingerprint, server_date,
            )
        if not isinstance(response.payload, Mapping) or not shape(response.payload):
            return IgReadinessRead(
                resource, endpoint_family, "FAIL",
                f"IG_READ_{resource}_RESPONSE_SHAPE_INVALID", "INVALID",
                started, observed, status_class, provider_code, request_fingerprint, server_date,
            )
        self._read_count += 1
        self._read_observations.append(IgReadObservation(
            resource=resource, request_started_at=started, response_observed_at=observed,
            server_date_utc=server_date, request_id_fingerprint=request_fingerprint,
        ))
        return IgReadinessRead(
            resource, endpoint_family, "PASS", "NONE", "VALID", started, observed,
            status_class, provider_code, request_fingerprint, server_date, response.payload,
        )

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


def _safe_provider_error(payload: object) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    return safe_provider_error_code(payload.get("errorCode"))


def safe_provider_error_code(candidate: object) -> str | None:
    """Return only an exact documented, credential-free provider code."""
    return candidate if isinstance(candidate, str) and candidate in _SAFE_ERROR_CODES else None


def _activity_query(
    from_utc: datetime, to_utc: datetime, page_size: int
) -> dict[str, str]:
    """Canonical IG activity-v3 query: UTC wall time at whole-second precision."""
    for value, name in ((from_utc, "from_utc"), (to_utc, "to_utc")):
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")
    start = from_utc.astimezone(timezone.utc)
    end = to_utc.astimezone(timezone.utc)
    if end <= start or end - start > timedelta(days=7):
        raise ValueError("account activity interval must be positive and at most 7 days")
    if type(page_size) is not int or not 10 <= page_size <= 500:
        raise ValueError("page_size must be between 10 and 500")
    return {
        "from": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "to": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "detailed": "true",
        "pageSize": str(page_size),
    }


def _http_status_class(status: int) -> str:
    return f"HTTP_{status // 100}XX" if 100 <= status <= 599 else "HTTP_OTHER"


def _mapping_list(payload: Mapping[str, object], name: str) -> list[object] | None:
    value = payload.get(name)
    return value if isinstance(value, list) else None


def _shape_accounts(payload: Mapping[str, object]) -> bool:
    values = _mapping_list(payload, "accounts")
    return values is not None and all(isinstance(value, Mapping) for value in values)


def _shape_positions(payload: Mapping[str, object]) -> bool:
    values = _mapping_list(payload, "positions")
    return values is not None and all(
        isinstance(value, Mapping)
        and isinstance(value.get("position"), Mapping)
        and isinstance(value.get("market"), Mapping)
        for value in values
    )


def _shape_working_orders(payload: Mapping[str, object]) -> bool:
    values = _mapping_list(payload, "workingOrders")
    return values is not None and all(
        isinstance(value, Mapping) and isinstance(value.get("workingOrderData"), Mapping)
        for value in values
    )


def _shape_market_v4(payload: Mapping[str, object]) -> bool:
    return all(isinstance(payload.get(name), Mapping) for name in (
        "instrument", "dealingRules", "snapshot"
    ))


def _shape_activity(payload: Mapping[str, object]) -> bool:
    metadata = payload.get("metadata")
    activities = _mapping_list(payload, "activities")
    return (activities is not None and all(isinstance(value, Mapping) for value in activities)
            and isinstance(metadata, Mapping) and isinstance(metadata.get("paging"), Mapping))


def _shape_prices(payload: Mapping[str, object]) -> bool:
    prices = _mapping_list(payload, "prices")
    if (prices is None or not all(isinstance(value, Mapping) for value in prices)
            or not isinstance(payload.get("metadata"), Mapping)):
        return False
    page_data = payload["metadata"].get("pageData")
    if page_data is None:
        return True
    if not isinstance(page_data, Mapping):
        return False
    pages = page_data.get("totalPages")
    return pages is None or (type(pages) is int and pages in (0, 1))
