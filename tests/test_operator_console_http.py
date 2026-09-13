"""Actual local sockets, offline fixture files, no database or broker connection."""
from contextlib import contextmanager
from datetime import datetime
import http.client
import importlib.util
import json
from pathlib import Path
import sys
import threading
from unittest.mock import Mock

import pytest

from daxlab.runtime.atomic_json import atomic_write_json
from test_operator_console_projection import console_sources


@pytest.fixture
def console_server(tmp_path, monkeypatch):
    path = Path("scripts/serve_operator_console.py")
    spec = importlib.util.spec_from_file_location("operator_http_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    raw, snapshot, hb, now, _ = console_sources()
    for name, data in (("latest_bundle.json", raw), ("candidate_operator_snapshot.json", snapshot), ("heartbeat.json", hb)):
        atomic_write_json(tmp_path / name, data)

    class FixedTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(module, "datetime", FixedTime)
    server = module.OperatorReadServer(state_dir=tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield module, server, tmp_path
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@contextmanager
def connection(server):
    c = http.client.HTTPConnection(*server.server_address, timeout=5)
    try:
        yield c
    finally:
        c.close()


def request(server, path="/api/operator", method="GET", headers=None):
    with connection(server) as c:
        c.request(method, path, headers=headers or {})
        response = c.getresponse()
        return response.status, dict(response.getheaders()), response.read()


def test_get_only_validated_credential_free_projection_on_real_local_socket(console_server):
    _, server, _ = console_server
    code, headers, body = request(server)
    view = json.loads(body)
    assert code == 200
    assert view["source_available"] is True
    assert view["execution_capability"] == "NONE"
    assert view["order_execution_enabled"] is False
    assert "no-store" in headers["Cache-Control"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers
    assert b"NEON_DATABASE_URL" not in body


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def test_control_methods_do_not_even_read_runtime_source(console_server, monkeypatch, method):
    module, server, _ = console_server
    source = Mock(side_effect=AssertionError("must not access source"))
    monkeypatch.setattr(module, "read_local_operator_projection", source)
    code, _, _ = request(server, method=method)
    assert code == 405
    source.assert_not_called()


@pytest.mark.parametrize("headers", [
    {"Host": "evil.example"}, {"Origin": "http://evil.example"},
    {"Sec-Fetch-Site": "cross-site"}, {"Host": "127.0.0.1:1"},
])
def test_dns_rebinding_or_cross_origin_cannot_read_runtime(console_server, monkeypatch, headers):
    module, server, _ = console_server
    source = Mock(side_effect=AssertionError("must not access source"))
    monkeypatch.setattr(module, "read_local_operator_projection", source)
    code, _, _ = request(server, headers=headers)
    assert code == 403
    source.assert_not_called()


@pytest.mark.parametrize("path", ["/api/order", "/api/start", "/api/operator?file=secret", "/../heartbeat.json", "/heartbeat.json", "/.env"])
def test_unknown_paths_cannot_read_control_or_state_files(console_server, path):
    _, server, _ = console_server
    assert request(server, path=path)[0] == 404


@pytest.mark.parametrize("content", ["{}", "[]", "{bad", '{"schema_version":"old","schema_version":"new"}', '{"age":NaN}', '{"age":Infinity}'])
def test_malformed_or_duplicate_json_discards_runtime_view(console_server, content):
    _, server, root = console_server
    (root / "candidate_operator_snapshot.json").write_text(content)
    code, _, body = request(server)
    assert code == 503
    view = json.loads(body)
    assert view["candidate"] is None
    assert view["source_available"] is False
    assert all(v["state"] != "GREEN" for v in view["system"].values())


def test_source_exception_and_credentials_are_never_sent_to_browser(console_server, monkeypatch):
    module, server, _ = console_server
    monkeypatch.setattr(module, "read_local_operator_projection", Mock(side_effect=OSError("postgresql://user:secret@neon/db /private/path")))
    code, _, body = request(server)
    assert code == 503
    assert b"secret" not in body and b"postgresql" not in body and b"/private" not in body
    assert json.loads(body)["provenance"]["runtime_safety_observed"] is False


def test_missing_source_or_alive_server_never_implies_host_ready(console_server):
    _, server, root = console_server
    (root / "heartbeat.json").unlink()
    code, _, body = request(server, path="/healthz")
    health = json.loads(body)
    assert code == 503
    assert health["process_responding"] is True
    assert health["source_available"] is False
    assert health["runtime_state"] != "GREEN"
    assert health["execution_authorized"] is False


def test_reader_never_creates_state_store_or_changes_source_bytes(console_server):
    module, server, root = console_server
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    request(server)
    request(server, path="/healthz")
    after = {p.name: p.read_bytes() for p in root.iterdir()}
    assert before == after
    absent = root / "not-existing"
    module.read_local_operator_projection(absent, queried_at=datetime.now().astimezone())
    assert not absent.exists()


def test_http_layer_has_no_database_mt5_store_write_or_submission_surface():
    import ast
    tree = ast.parse(Path("scripts/serve_operator_console.py").read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(n and n.startswith(("MetaTrader5", "psycopg", "daxlab.db")) for n in imports)
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not attrs & {"order_send", "order_check", "save", "initialize", "orders_get", "positions_get"}


def test_moving_heartbeat_is_rejected_without_retries_or_persistence(console_server, monkeypatch):
    module, _, root = console_server
    original = Path.read_bytes
    count = 0

    def moving(path):
        nonlocal count
        result = original(path)
        if path.name == "heartbeat.json":
            count += 1
            if count == 2:
                return result + b" "
        return result

    monkeypatch.setattr(Path, "read_bytes", moving)
    with pytest.raises(ValueError, match="changed during read"):
        module.read_local_operator_projection(root, queried_at=datetime.now().astimezone())
    assert count == 2
