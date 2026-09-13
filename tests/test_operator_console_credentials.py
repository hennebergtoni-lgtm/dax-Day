"""Synthetic secrets only; actual loopback HTTP response regression tests."""
from dataclasses import fields, replace
from pathlib import Path

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.operator_snapshot import parse_operator_snapshot_payload
from test_operator_console_http import console_server as console_server, request


@pytest.mark.parametrize("value", [
    "Authorization: Bearer SYNTHETIC_ONLY_SECRET",
    "api token=SYNTHETIC_ONLY_SECRET", "access_token=SYNTHETIC_ONLY_SECRET",
    "postgresql://test:SYNTHETIC_ONLY_SECRET@example.invalid/db",
    "https://test:SYNTHETIC_ONLY_SECRET@example.invalid",
    "-----BEGIN RSA PRIVATE KEY----- SYNTHETIC_ONLY_SECRET",
])
def test_secret_strings_never_reach_actual_http_response(console_server, value):
    _, server, root = console_server
    snapshot = read_json_object(root / "candidate_operator_snapshot.json")
    snapshot["runtime"]["events"] = [value]
    atomic_write_json(root / "candidate_operator_snapshot.json", snapshot)
    code, _, body = request(server)
    assert code == 503
    assert b"SYNTHETIC_ONLY_SECRET" not in body
    assert b"PRIVATE KEY" not in body


@pytest.mark.parametrize("key", ["PaSsWoRd", "LoGiN", "ACCOUNT-NUMBER", "Api_Token",
                                 "ſecret", "ACCESS-TOKEN", "Private Key"])
def test_nested_secret_keys_casefold_and_normalize_fail_closed(console_server, key):
    _, server, root = console_server
    heartbeat = read_json_object(root / "heartbeat.json")
    heartbeat["extra"] = [{"ordinary": [{key: "SYNTHETIC_ONLY_SECRET"}]}]
    atomic_write_json(root / "heartbeat.json", heartbeat)
    code, _, body = request(server)
    assert code == 503
    assert b"SYNTHETIC_ONLY_SECRET" not in body


def test_opaque_free_text_is_structurally_redacted_without_secret_heuristics(console_server):
    _, server, root = console_server
    path = root / "candidate_operator_snapshot.json"
    snapshot = replace(parse_operator_snapshot_payload(read_json_object(path)),
                       runtime_events=("UNRECOGNIZED_OPAQUE_SENTINEL",))
    snapshot = replace(snapshot, snapshot_fingerprint=stable_fingerprint({
        f.name: getattr(snapshot, f.name) for f in fields(snapshot)
        if f.name != "snapshot_fingerprint"
    }))
    atomic_write_json(path, snapshot.as_dict())
    code, _, body = request(server)
    assert code == 200
    assert b"UNRECOGNIZED_OPAQUE_SENTINEL" not in body
    assert b"REDACTED_UNRECOGNIZED_TEXT" in body
    assert read_json_object(path) == snapshot.as_dict()


def test_no_credentials_added_to_browser_assets():
    body = "".join(Path(p).read_text() for p in
                   ("web/operator.html", "web/operator.js", "web/operator.css"))
    assert "postgresql://" not in body and "NEON_DATABASE_URL" not in body
