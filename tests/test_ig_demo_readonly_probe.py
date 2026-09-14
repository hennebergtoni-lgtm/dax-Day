from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from daxlab.adapters.ig_market_data import IgClosedM5CandleSource, IgClosedM5Feed, ig_m5_interval
from daxlab.adapters.ig_rest_readonly import IgDemoCredentials, IgDemoReadOnlyClient, JsonResponse
from daxlab.domain.market import InstrumentId
from test_ig_rest_readonly import FakeTransport, _login_response


_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ig_demo_readonly_probe.py"
_SPEC = importlib.util.spec_from_file_location("ig_probe_test", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe)
EPIC = "IX.D.DAX.IFMM.IP"


def price_row(close_time: datetime, value: float = 100.0) -> dict[str, object]:
    return {
        "snapshotTimeUTC": close_time.isoformat(),
        "openPrice": {"bid": value, "ask": value + 2},
        "highPrice": {"bid": value + 4, "ask": value + 6},
        "lowPrice": {"bid": value - 4, "ask": value - 2},
        "closePrice": {"bid": value + 1, "ask": value + 3},
    }


def observed_prices() -> list[dict[str, object]]:
    start = datetime(2026, 9, 14, 8, 20, tzinfo=timezone.utc)
    return [price_row(start + timedelta(minutes=5 * n), 100.0 + n) for n in range(9)]


def test_old_future_label_report_is_rejected_under_final_interval_start_contract() -> None:
    # The prior interval-end fixture is retained as an incompatible historical assumption.
    rows = [*observed_prices(), price_row(datetime(2026, 9, 14, 9, 5, tzinfo=timezone.utc))]
    with pytest.raises(ValueError, match="extends beyond the current M5 interval"):
        probe._closed_candles(
            {"prices": rows},
            epic=EPIC,
            instrument_id="DAX",
            observed_at=datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc),
        )


def test_raw_0900_is_active_at_090259_and_excluded() -> None:
    candles = probe._closed_candles(
        {"prices": observed_prices()},
        epic=EPIC,
        instrument_id="DAX",
        observed_at=datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc),
    )
    assert len(candles) == 8
    assert candles[-1]["snapshot_time_utc"] == "2026-09-14T08:55:00+00:00"
    assert candles[-1]["event_time"] == "2026-09-14T08:55:00+00:00"
    assert candles[-1]["close_time"] == "2026-09-14T09:00:00+00:00"


def test_history_page_size_is_explicitly_disabled() -> None:
    transport = FakeTransport([_login_response()])
    client = IgDemoReadOnlyClient(IgDemoCredentials("demo", "secret", "key"), transport)
    client.login()
    transport.responses.append(JsonResponse(200, {}, {"prices": []}))
    client.m5_prices(EPIC, max_bars=40)
    assert transport.calls[-1]["query"] == {
        "resolution": "MINUTE_5", "max": "40", "pageSize": "0",
    }


@pytest.mark.parametrize(("seconds", "expected_count", "latest"), [
    (-1, 8, "09:00:00"), (0, 9, "09:05:00"), (1, 9, "09:05:00"),
])
def test_exact_m5_boundary(seconds, expected_count, latest) -> None:
    now = datetime(2026, 9, 14, 9, 5, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    candles = probe._closed_candles({"prices": observed_prices()}, epic=EPIC,
                                   instrument_id="DAX", observed_at=now)
    assert len(candles) == expected_count
    assert candles[-1]["close_time"] == f"2026-09-14T{latest}+00:00"


def test_request_crossing_boundary_does_not_relabel_incomplete_response() -> None:
    candles = probe._closed_candles(
        {"prices": observed_prices()}, epic=EPIC, instrument_id="DAX",
        closed_as_of=datetime(2026, 9, 14, 9, 4, 59, tzinfo=timezone.utc),
        observed_at=datetime(2026, 9, 14, 9, 5, 1, tzinfo=timezone.utc),
    )
    assert candles[-1]["close_time"] == "2026-09-14T09:00:00+00:00"
    assert len(candles) == 8


def test_request_clock_reverse_is_blocked() -> None:
    with pytest.raises(ValueError, match="clock moved backwards"):
        probe._closed_candles({"prices": observed_prices()}, epic=EPIC, instrument_id="DAX",
                             closed_as_of=datetime(2026, 9, 14, 9, 5, tzinfo=timezone.utc),
                             observed_at=datetime(2026, 9, 14, 9, 4, tzinfo=timezone.utc))


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(microseconds=1)])
def test_existing_freshness_limit_is_measured_from_interval_end(offset) -> None:
    now = datetime(2026, 9, 14, 9, 10, tzinfo=timezone.utc) + offset
    kwargs = dict(prices_payload={"prices": [observed_prices()[-2]]}, epic=EPIC,
                  instrument_id="DAX", observed_at=now)
    if offset:
        with pytest.raises(ValueError, match="fresh M5 data"):
            probe._closed_candles(**kwargs)
    else:
        assert probe._closed_candles(**kwargs)[0]["close_time"] == "2026-09-14T09:00:00+00:00"


def test_full_40_bar_response_avoids_old_first_page_staleness() -> None:
    end = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
    rows = [price_row(end - timedelta(minutes=5*n)) for n in reversed(range(40))]
    now = datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="fresh M5 data"):
        probe._closed_candles({"prices": rows[:20]}, epic=EPIC, instrument_id="DAX", observed_at=now)
    candles = probe._closed_candles({"prices": rows}, epic=EPIC, instrument_id="DAX", observed_at=now)
    assert len(candles) == 39
    assert candles[-1]["close_time"] == "2026-09-14T09:00:00+00:00"


@pytest.mark.parametrize(("wire", "event"), [
    ("2026-03-29T03:00:00+02:00", datetime(2026, 3, 29, 1, tzinfo=timezone.utc)),
    ("2026-10-25T02:00:00+01:00", datetime(2026, 10, 25, 1, tzinfo=timezone.utc)),
    ("2026-09-14T09:00:00", datetime(2026, 9, 14, 9, tzinfo=timezone.utc)),
])
def test_utc_and_dst_are_absolute_intervals(wire, event) -> None:
    row = price_row(event)
    row["snapshotTimeUTC"] = wire
    opened, ended = ig_m5_interval(row)
    assert opened == event
    assert ended == event + timedelta(minutes=5)
    assert opened.utcoffset() == ended.utcoffset() == timedelta(0)


@pytest.mark.parametrize("rows", [
    [{"snapshotTime": "2026/09/14 09:00:00"}],
    [{"snapshotTimeUTC": "not-a-time"}],
    [{"snapshotTimeUTC": "2026-09-14T09:02:00Z"}],
    [{"snapshotTimeUTC": "2026-09-14T09:00:01Z"}],
    [None], [],
    [observed_prices()[0], observed_prices()[0]],
    list(reversed(observed_prices())),
    [observed_prices()[0], observed_prices()[2]],
    [price_row(datetime(2026, 9, 14, 9, 15, tzinfo=timezone.utc))],
])
def test_malformed_gapped_unordered_or_implausible_future_history_fails_closed(rows) -> None:
    with pytest.raises(ValueError):
        probe._closed_candles({"prices": rows}, epic=EPIC, instrument_id="DAX",
                             observed_at=datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc))


def test_naive_observation_is_not_interpreted_as_machine_local_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        probe._closed_candles({"prices": observed_prices()}, epic=EPIC,
                             instrument_id="DAX", observed_at=datetime(2026, 9, 14, 9, 2, 59))


def test_source_itself_filters_the_live_tail_and_never_replays_closed_rows() -> None:
    feed = IgClosedM5Feed(EPIC, datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc), observed_prices())
    source = IgClosedM5CandleSource(lambda: feed, EPIC, InstrumentId("DAX"))
    candles = []
    while (candle := source.next_candle()) is not None:
        candles.append(candle)
    assert len(candles) == 8
    assert candles[-1].close_time == datetime(2026, 9, 14, 9, tzinfo=timezone.utc)
    assert source.next_candle() is None


def market_payload() -> dict[str, object]:
    return {"instrument": {"epic": EPIC, "name": "Germany 40", "type": "INDICES",
                           "lotSize": 1, "valueOfOnePip": "1.00", "onePipMeans": "1 Index Point"},
            "dealingRules": {"minDealSize": {"unit": "POINTS", "value": 1}},
            "snapshot": {"marketStatus": "TRADEABLE", "bid": 100.0, "offer": 102.0,
                         "updateTimeUTC": "09:02:58"}}


def collect_fixture(tmp_path, monkeypatch, *, positions=None, orders=None, market=None, accounts=None):
    path = tmp_path / "credentials.env"
    path.write_text("IG_USERNAME=synthetic-login\nIG_PASSWORD=synthetic-password\nIG_API_KEY=synthetic-key\n")
    transport = FakeTransport([
        _login_response(), JsonResponse(200, {}, accounts or {"accounts": [{"accountType": "CFD", "currency": "EUR", "preferred": True}]}),
        JsonResponse(200, {}, {"positions": positions or []}),
        JsonResponse(200, {}, {"workingOrders": orders or []}),
        JsonResponse(200, {}, market or market_payload()),
        JsonResponse(200, {}, {"prices": observed_prices(), "metadata": {"pageData": {"totalPages": 1}}}),
        JsonResponse(200, {}, {}),
    ])
    clients = []
    def client_factory(*, credentials):
        client = IgDemoReadOnlyClient(credentials, transport)
        clients.append(client)
        return client
    monkeypatch.setattr(probe, "IgDemoReadOnlyClient", client_factory)
    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 14, 9, 2, 59, tzinfo=timezone.utc).astimezone(tz)
    monkeypatch.setattr(probe, "datetime", FixedClock)
    result = probe.collect_probe(credentials_file=path, epic=EPIC, instrument_id="DAX", bars=40)
    assert clients[0].authenticated is False
    return result, transport


@pytest.mark.parametrize("count", [0, 1, 3])
def test_probe_reports_full_account_counts_without_claiming_recon_or_protection(tmp_path, monkeypatch, count) -> None:
    view, transport = collect_fixture(tmp_path, monkeypatch,
                                      positions=[{"position": {"dealId": "manual"}}]*count,
                                      orders=[{"workingOrderData": {"dealId": "foreign"}}]*count)
    assert view["environment"] == "IG_DEMO"
    assert view["open_positions_count"] == view["working_orders_count"] == count
    assert view["execution_capability"] == "NONE" and view["order_execution_enabled"] is False
    assert view["reconciliation_state"] == view["protection_state"] == "UNKNOWN"
    assert view["inventory_history_complete"] is False and view["inventory_is_atomic"] is False
    assert view["inventory_freshness_threshold"] == "UNVERIFIED_THRESHOLD"
    assert view["market"]["quote_freshness_state"] == "UNKNOWN"
    assert view["raw_m5_count"] == 9 and view["closed_m5_count"] == 8 and view["not_closed_m5_count"] == 1
    assert view["latest_closed_m5_age_seconds"] == 179.0
    assert view["m5_freshness_max_age_seconds"] == 600.0
    assert view["m5_freshness_basis"] == "TRUE_CLOSE_TIME"
    assert view["m5_market_data_contract"]["raw_timestamp_semantics"] == "INTERVAL_START"
    digest = view.pop("fingerprint")
    assert digest == probe._fingerprint(view)
    assert [c["method"] for c in transport.calls] == ["POST", "GET", "GET", "GET", "GET", "GET", "DELETE"]
    assert all(c["url"].endswith("/session") or c["method"] == "GET" for c in transport.calls)


@pytest.mark.parametrize("secret", ["Bearer SYNTHETIC_SENTINEL", "postgres://user:pass@host/db",
                                    "-----BEGIN PRIVATE KEY-----", "api_token=SYNTHETIC_SENTINEL"])
def test_nested_malicious_fields_and_free_form_metadata_cannot_leak(tmp_path, monkeypatch, secret) -> None:
    market = market_payload()
    market["instrument"].update({"name": secret, "type": secret, "valueOfOnePip": secret,
                                 "PASSWORD": {"nested": [{"Authorization": secret}]}})
    market["dealingRules"]["minDealSize"].update({"SECRET": [{"secret": secret}], "unit": secret})
    market["snapshot"].update({"marketStatus": secret, "updateTimeUTC": secret})
    accounts = {"accounts": [{"accountId": secret, "login": secret, "accountType": secret,
                              "currency": {"token": secret}, "preferred": {"api_key": secret},
                              "balance": {"balance": secret, "profitLoss": float("nan")}}]}
    view, _ = collect_fixture(tmp_path, monkeypatch, market=market, accounts=accounts)
    rendered = json.dumps(view, allow_nan=False)
    assert secret not in rendered
    assert "synthetic-login" not in rendered and "synthetic-password" not in rendered and "synthetic-key" not in rendered
    assert view["market"]["name"] is None
    assert view["accounts"][0]["account_type"] is None


@pytest.mark.parametrize("key", ["positions", "workingOrders"])
def test_malformed_inventory_is_not_counted_as_observed_objects(key) -> None:
    with pytest.raises(RuntimeError, match="inventory entry"):
        probe._inventory_count({key: [None]}, key)


def test_cli_failure_does_not_echo_provider_secret_or_write_success_evidence(tmp_path, monkeypatch, capsys) -> None:
    def fail(**kwargs):
        raise RuntimeError("Bearer SYNTHETIC_SENTINEL")
    monkeypatch.setattr(probe, "collect_probe", fail)
    output = tmp_path / "evidence.json"
    monkeypatch.setattr(sys, "argv", ["probe", "--credentials-file", "unused", "--output", str(output)])
    assert probe.main() == 2
    text = capsys.readouterr().out
    assert "SYNTHETIC_SENTINEL" not in text
    assert json.loads(text)["evidence_state"] == "BLOCKED"
    assert not output.exists()


@pytest.mark.parametrize("key", ["AuthoriZation", "API-KEY", "AccountId", "LOGIN", "private_key"])
def test_credential_defense_rejects_nested_malicious_key_casing(key) -> None:
    with pytest.raises(RuntimeError, match="forbidden evidence key"):
        probe._assert_credential_free({"nested": [{key: "SYNTHETIC_SENTINEL"}]})


def test_unknown_market_name_does_not_remove_valid_numeric_economics() -> None:
    payload = market_payload()
    payload["instrument"]["name"] = "unreviewed market display text"
    result = probe._safe_market(payload, expected_epic=EPIC)
    assert result["name"] is None
    assert result["value_of_one_pip"] == 1.0
    assert result["one_pip_means"] == "1 Index Point"


def test_local_quote_update_time_is_not_silently_relabelled_utc() -> None:
    payload = market_payload()
    payload["snapshot"].pop("updateTimeUTC")
    payload["snapshot"]["updateTime"] = "10:02:58"
    result = probe._safe_market(payload, expected_epic=EPIC)
    assert result["update_time_utc"] is None
    assert result["quote_freshness_state"] == "UNKNOWN"
