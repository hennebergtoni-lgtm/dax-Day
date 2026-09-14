from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import io

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("export_raw", ROOT / "scripts/export_ig_raw_truth_2233.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def originals():
    start = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    captures = {}
    for index, name in enumerate("ABC"):
        requested = start + timedelta(minutes=1 + 5 * index)
        rows = []
        for offset in range(4):
            timestamp = start + timedelta(minutes=5 * (index + offset - 3))
            quote = {"bid": 100.0, "ask": 102.0, "lastTraded": None}
            rows.append({"snapshotTimeUTC": timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                         **{field: dict(quote) for field in module.raw.PRICE_FIELDS},
                         "lastTradedVolume": index + offset})
        captures[name] = module.raw.snapshot(rows, head=module.EVIDENCE_HEAD,
                                             requested=requested,
                                             observed=requested + timedelta(seconds=1))
    payloads = {name + ".json": item for name, item in captures.items()}
    for pair in ("AB", "BC"):
        payloads[pair + ".json"] = module.raw.compare(captures[pair[0]], captures[pair[1]])
    summary = {
        "schema": "DAX_IG_RAW_TRUTH_ATTEMPT_V2", "exact_head": module.EVIDENCE_HEAD,
        "attempt_namespace": module.NAMESPACE,
        "session": {"model": "ONE_LOGIN_IN_MEMORY_V1", "login_attempted": True,
                    "login_success": True, "cleanup_attempted": True,
                    "cleanup_success": True, "cleanup_error_code": None},
        "started_at": start.isoformat(), "finished_at": (start + timedelta(minutes=12)).isoformat(),
        "sampling_offset_seconds": 60, "sampling_window_seconds": 60,
        "raw": {name: {"scheduled_at": item["request_started_at_utc"],
                       "invoked_at": item["request_started_at_utc"], "requested": True,
                       "success": True, "exit": 0, "status": "SUCCESS",
                       "request_started_at_utc": item["request_started_at_utc"],
                       "response_observed_at_utc": item["response_observed_at_utc"],
                       "fingerprint": item["fingerprint"]} for name, item in captures.items()},
        "compare": {pair: {"status": "SUCCESS", "exit": 0,
                           "fingerprint": payloads[pair + ".json"]["fingerprint"]}
                    for pair in ("AB", "BC")},
        "final_state": "SUCCESS", "error_code": None, "execution_capability": "NONE",
        "order_execution_enabled": False, "candidate_processing_performed": False,
        "timestamp_semantics": "UNKNOWN", "classification_state": "UNVERIFIED",
    }
    summary["fingerprint"] = module.raw._fingerprint(summary)
    payloads["SUMMARY.json"] = summary
    return {name: (json.dumps(item, indent=3) + "\r\n").encode() for name, item in payloads.items()}


def test_original_bytes_and_hashes_preserved_without_semantics_promotion():
    source = originals()
    data, manifest = module.bundle_bytes(source, runtime_head="a" * 40)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert set(archive.namelist()) == set(module.FILES) | {"MANIFEST.json", "REVIEW.json"}
        for name in module.FILES:
            assert archive.read(name) == source[name]
            assert manifest["files"][name]["sha256"] == hashlib.sha256(source[name]).hexdigest()
        report = json.loads(archive.read("REVIEW.json"))
        assert report["classification"] == "OTHER_UNKNOWN"
        assert report["revision_bound_seconds"] is None
        assert report["candidate_processing_performed"] is False


@pytest.mark.parametrize("name", module.FILES)
def test_missing_file_blocks(name):
    source = originals()
    del source[name]
    with pytest.raises(module.ExportBlocked):
        module.bundle_bytes(source, runtime_head="a" * 40)


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(secret={"password": "SECRET"}),
    lambda s: s["session"].update(token="SECRET"),
    lambda s: s["raw"]["A"].update(status="Bearer SECRET"),
    lambda s: s.update(execution_capability="DEMO_ONLY"),
    lambda s: s.update(candidate_processing_performed=True),
    lambda s: s["raw"]["B"].update(fingerprint="0" * 64),
])
def test_rehashed_summary_injection_and_identity_drift_block(mutation):
    source = originals()
    summary = json.loads(source["SUMMARY.json"])
    mutation(summary)
    summary.pop("fingerprint")
    summary["fingerprint"] = module.raw._fingerprint(summary)
    source["SUMMARY.json"] = json.dumps(summary).encode()
    with pytest.raises(module.ExportBlocked):
        module.bundle_bytes(source, runtime_head="a" * 40)


def test_corrupted_compare_blocks():
    source = originals()
    compare = json.loads(source["AB.json"])
    compare["changed_raw_timestamp_count"] = 1
    source["AB.json"] = json.dumps(compare).encode()
    with pytest.raises(module.ExportBlocked):
        module.bundle_bytes(source, runtime_head="a" * 40)


def test_duplicate_key_and_size_limit():
    with pytest.raises(module.ExportBlocked):
        module.decode(b'{"schema": 1, "schema": 2}')
    with pytest.raises(module.ExportBlocked):
        module.decode(b" " * (module.MAX_BYTES + 1))


def test_export_exclusive_and_no_source_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(module.raw, "check_code", lambda head: head)
    source = originals()
    directory = tmp_path / module.NAMESPACE
    directory.mkdir(parents=True)
    for name, data in source.items():
        (directory / name).write_bytes(data)
    output, _ = module.export("a" * 40, root=tmp_path)
    before = output.read_bytes()
    with pytest.raises(module.ExportBlocked):
        module.export("a" * 40, root=tmp_path)
    assert output.read_bytes() == before
    assert all((directory / name).read_bytes() == data for name, data in source.items())


def test_symlink_source_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(module.raw, "check_code", lambda head: head)
    directory = tmp_path / module.NAMESPACE
    directory.mkdir(parents=True)
    target = tmp_path / "outside"
    target.write_bytes(b"SECRET")
    (directory / "A.json").symlink_to(target)
    with pytest.raises(module.ExportBlocked):
        module.export("a" * 40, root=tmp_path)


def test_cli_failure_does_not_render_provider_or_secret_text(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("Bearer SECRET")
    monkeypatch.setattr(module, "export", fail)
    assert module.main(["--expected-head", "a" * 40]) == 2
    assert "SECRET" not in capsys.readouterr().out
