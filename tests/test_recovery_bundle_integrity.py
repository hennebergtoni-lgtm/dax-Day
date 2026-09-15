"""Canonical bundle completeness and semantic integrity under valid file hashes."""
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from daxlab.runtime.checkpoint import ReplayCheckpoint
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest
from daxlab.runtime.recovery_bundle import (
    RecoveryBundleManifest, verify_recovery_bundle, write_recovery_bundle,
)


PAYLOADS = (
    "bundle_manifest.json", "run_manifest.json", "checkpoint.json", "decision_log_manifest.json",
)


def _surface():
    run = RunManifest.build(
        dataset_fingerprint="data-A", engine_fingerprint="engine", config={"x": 1},
        mode=RuntimeMode.REPLAY,
    )
    log = DecisionLogManifest(2, 1, 1, "log-A")
    checkpoint = ReplayCheckpoint.build(
        run_manifest=run, processed_candles=103,
        last_event_time_iso="2026-09-08T17:30:00+02:00", decision_log=log,
    )
    bundle = RecoveryBundleManifest.build(
        source_commit_sha="abc123", run_manifest=run, checkpoint=checkpoint,
        decision_log=log, status="COMPLETED",
    )
    return bundle, run, checkpoint, log


@pytest.fixture
def directory(tmp_path):
    bundle, run, checkpoint, log = _surface()
    write_recovery_bundle(
        tmp_path, bundle=bundle, run_manifest=run, checkpoint=checkpoint, decision_log=log,
    )
    return tmp_path


def _reseal(directory: Path, names=PAYLOADS):
    """Create correct byte hashes even when the retained payload semantics are invalid."""
    (directory / "SHA256SUMS").write_text("".join(
        f"{sha256((directory / name).read_bytes()).hexdigest()}  {name}\n" for name in names
    ), encoding="utf-8")


def _change(directory, filename, **fields):
    target = directory / filename
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload.update(fields)
    target.write_text(json.dumps(payload), encoding="utf-8")
    _reseal(directory)


def test_valid_canonical_bundle_control(directory):
    assert {p.name for p in directory.iterdir()} == {*PAYLOADS, "SHA256SUMS"}
    assert verify_recovery_bundle(directory) is None


def test_empty_directory_is_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="checksums missing"):
        verify_recovery_bundle(tmp_path)


@pytest.mark.parametrize("retained_payloads", [False, True])
def test_empty_checksums_are_rejected(directory, retained_payloads):
    if not retained_payloads:
        for name in PAYLOADS:
            (directory / name).unlink()
    (directory / "SHA256SUMS").write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="file list incomplete"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("name", [*PAYLOADS, "SHA256SUMS"])
def test_every_missing_required_file_is_rejected(directory, name):
    (directory / name).unlink()
    with pytest.raises(RuntimeError, match="missing"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("name", PAYLOADS)
@pytest.mark.parametrize("remove_payload", [False, True])
def test_omitted_checksum_entry_is_rejected(directory, name, remove_payload):
    if remove_payload:
        (directory / name).unlink()
    _reseal(directory, [other for other in PAYLOADS if other != name])
    with pytest.raises(RuntimeError, match="file list incomplete"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("name", [
    "arbitrary.json", "../checkpoint.json", "/tmp/checkpoint.json", "./checkpoint.json",
    "sub/checkpoint.json", r"..\checkpoint.json", "checkpoint.json ", "SHA256SUMS",
])
def test_replacement_or_unsafe_checksum_filename_is_rejected(directory, name):
    target = directory / "SHA256SUMS"
    text = target.read_text(encoding="utf-8").replace("  checkpoint.json\n", f"  {name}\n")
    target.write_text(text, encoding="utf-8")
    with pytest.raises(RuntimeError, match="filename"):
        verify_recovery_bundle(directory)


def test_duplicate_checksum_entry_is_rejected(directory):
    target = directory / "SHA256SUMS"
    text = target.read_text(encoding="utf-8")
    target.write_text(text + text.splitlines()[0] + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("line", ["not-a-checksum", "z" * 64 + "  checkpoint.json", "\n"])
def test_malformed_checksum_entry_is_rejected(directory, line):
    with (directory / "SHA256SUMS").open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")
    with pytest.raises(RuntimeError, match="checksum entry"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("name", [*PAYLOADS, "SHA256SUMS"])
def test_symlink_required_file_is_rejected(directory, name, tmp_path_factory):
    target = directory / name
    outside = tmp_path_factory.mktemp("outside") / name
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(RuntimeError, match="missing"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize(("filename", "fields", "message"), [
    ("bundle_manifest.json", {"schema_version": "OTHER"}, "schema mismatch"),
    ("bundle_manifest.json", {"status": "RUNNING"}, "invalid recovery bundle status"),
    ("bundle_manifest.json", {"source_commit_sha": ""}, "identities"),
    ("bundle_manifest.json", {"run_manifest_fingerprint": "other"}, "run-manifest mismatch"),
    ("bundle_manifest.json", {"checkpoint_fingerprint": "other"}, "checkpoint fingerprint"),
    ("bundle_manifest.json", {"decision_log_fingerprint": "log-B"}, "decision-log mismatch"),
    ("run_manifest.json", {"manifest_fingerprint": "other"}, "fingerprint drift"),
    ("run_manifest.json", {"dataset_fingerprint": "data-B"}, "fingerprint drift"),
    ("run_manifest.json", {"mode": "UNKNOWN"}, "invalid recovery bundle payload"),
    ("checkpoint.json", {"run_manifest_fingerprint": "other"}, "run-manifest mismatch"),
    ("checkpoint.json", {"processed_candles": 104}, "checkpoint fingerprint"),
    ("checkpoint.json", {"processed_candles": -1}, "processed_candles"),
    ("checkpoint.json", {"decision_log_fingerprint": "log-B"}, "decision-log mismatch"),
    ("decision_log_manifest.json", {"decision_ids_fingerprint": "log-B"}, "decision-log mismatch"),
    ("decision_log_manifest.json", {"decisions": 3}, "counts are inconsistent"),
    ("decision_log_manifest.json", {"trades": True}, "counts must"),
    ("checkpoint.json", {"unknown_field": "value"}, "invalid recovery bundle payload"),
])
def test_resealed_semantic_corruption_is_rejected(directory, filename, fields, message):
    _change(directory, filename, **fields)
    with pytest.raises(RuntimeError, match=message):
        verify_recovery_bundle(directory)


def test_actual_run_a_checkpoint_b_is_rejected_by_builder_and_verifier(directory):
    bundle, run, checkpoint, log = _surface()
    other_run = RunManifest.build(
        dataset_fingerprint="data-B", engine_fingerprint="engine", config={"x": 2},
        mode=RuntimeMode.REPLAY,
    )
    other_checkpoint = ReplayCheckpoint.build(
        run_manifest=other_run, processed_candles=103,
        last_event_time_iso=checkpoint.last_event_time_iso, decision_log=log,
    )
    with pytest.raises(RuntimeError, match="run-manifest mismatch"):
        RecoveryBundleManifest.build(
            source_commit_sha=bundle.source_commit_sha, run_manifest=run,
            checkpoint=other_checkpoint, decision_log=log, status="COMPLETED",
        )
    _change(directory, "checkpoint.json", **asdict(other_checkpoint))
    with pytest.raises(RuntimeError, match="run-manifest mismatch"):
        verify_recovery_bundle(directory)


def test_bundle_a_checkpoint_b_writer_rejects_before_any_write(tmp_path):
    bundle, run, checkpoint, log = _surface()
    other_checkpoint = replace(checkpoint, processed_candles=104)
    destination = tmp_path / "not-created"
    with pytest.raises(RuntimeError, match="checkpoint fingerprint mismatch"):
        write_recovery_bundle(
            destination, bundle=bundle, run_manifest=run,
            checkpoint=other_checkpoint, decision_log=log,
        )
    assert not destination.exists()


def test_decision_log_a_b_cross_binding_is_rejected(directory):
    bundle, run, checkpoint, log = _surface()
    other_log = replace(log, decision_ids_fingerprint="log-B")
    with pytest.raises(RuntimeError, match="checkpoint decision-log mismatch"):
        RecoveryBundleManifest.build(
            source_commit_sha=bundle.source_commit_sha, run_manifest=run,
            checkpoint=checkpoint, decision_log=other_log, status="COMPLETED",
        )
    _change(directory, "decision_log_manifest.json", **asdict(other_log))
    _change(directory, "bundle_manifest.json", decision_log_fingerprint="log-B")
    with pytest.raises(RuntimeError, match="checkpoint decision-log mismatch"):
        verify_recovery_bundle(directory)


@pytest.mark.parametrize("raw", [
    b"{}", b"[]", b"not-json", b'{"status":"COMPLETED","status":"ABORTED"}',
    b'{"processed_candles":NaN}', b'{"processed_candles":1e999}',
])
def test_invalid_json_structure_is_rejected_even_with_valid_hash(directory, raw):
    (directory / "checkpoint.json").write_bytes(raw)
    _reseal(directory)
    with pytest.raises(RuntimeError, match="invalid recovery bundle payload"):
        verify_recovery_bundle(directory)


def test_windows_newline_translation_cannot_change_published_bundle_bytes(tmp_path, monkeypatch):
    """Simulate Windows text writes; bundle hashes cover exact stored UTF-8 bytes."""
    def windows_write_text(path, text, encoding=None, errors=None, newline=None):
        encoded = text.replace("\n", "\r\n").encode(encoding or "utf-8")
        path.write_bytes(encoded)
        return len(text)

    monkeypatch.setattr(Path, "write_text", windows_write_text)
    control = tmp_path / "text-control"
    control.write_text("Windows\n", encoding="utf-8")
    assert control.read_bytes() == b"Windows\r\n"
    destination = tmp_path / "bundle"
    bundle, run, checkpoint, log = _surface()
    hashes = write_recovery_bundle(
        destination, bundle=bundle, run_manifest=run, checkpoint=checkpoint, decision_log=log,
    )
    assert verify_recovery_bundle(destination) is None
    for name in (*PAYLOADS, "SHA256SUMS"):
        stored = (destination / name).read_bytes()
        assert stored.endswith(b"\n") and b"\r\n" not in stored
        if name in hashes:
            assert hashes[name] == sha256(stored).hexdigest()
    # Verification must still detect byte changes rather than normalize CRLF.
    target = destination / "checkpoint.json"
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    with pytest.raises(RuntimeError, match="hash mismatch"):
        verify_recovery_bundle(destination)
