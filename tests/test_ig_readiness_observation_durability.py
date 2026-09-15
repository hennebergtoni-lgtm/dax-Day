"""Actual collector persistence and V3 contract regressions, synthetic I/O only."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.runtime.ig_predemo_safety import bind_ig_risk_session_inputs
from test_run_ig_predemo_readiness_2238 import MatrixClient, ROOT, runner

HEAD = "a" * 40


def finalized(client=None, writer=None):
    result, _ = runner.collect(
        client or MatrixClient(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40,
        observation_writer=writer,
    )
    return runner._finalize_evidence(result, cleanup_status="PASS", cleanup_error_code="NONE")[0]


def test_actual_v3_collector_binds_without_schema_relabel_or_unknown_upgrade():
    evidence = finalized()
    original = json.dumps(evidence, sort_keys=True)
    binding = bind_ig_risk_session_inputs(evidence, instrument_id=InstrumentId("DAX"))
    assert binding.source_fingerprint == evidence["fingerprint"]
    assert binding.instrument is None
    assert "QUANTITY_INCREMENT_UNVERIFIED" in binding.blockers
    assert "HISTORY_SCOPE_INCOMPLETE" not in binding.blockers
    assert evidence["history_scope"]["absolute_complete"] is False
    assert json.dumps(evidence, sort_keys=True) == original
    with pytest.raises(ValueError, match="instrument binding"):
        bind_ig_risk_session_inputs(evidence, instrument_id=InstrumentId("GOLD"))


@pytest.mark.parametrize("resource", [name for name, _ in runner.READ_RESOURCE_CONTRACTS])
def test_partial_v3_matrix_preserves_each_resource_blocker(resource):
    evidence = finalized(MatrixClient(raise_resource=resource))
    binding = bind_ig_risk_session_inputs(evidence, instrument_id=InstrumentId("DAX"))
    assert f"IG_READ_{resource}_UNVERIFIED" in binding.blockers
    assert binding.instrument is None


def test_raw_records_survive_failed_derived_publication(tmp_path):
    writer = runner.ReadinessObservationWriter(tmp_path / "raw", head=HEAD, evidence_scope="SYNTHETIC")
    writer.start()
    try:
        evidence = finalized(writer=writer)
        before = {p.name: p.read_bytes() for p in writer.namespace.iterdir()}
        with pytest.raises(OSError, match="transfer"):
            runner._publish(tmp_path / "derived", evidence, {}, head=HEAD, synthetic_sink=lambda files: {})
        assert {p.name: p.read_bytes() for p in writer.namespace.iterdir()} == before
        assert (tmp_path / "derived/READINESS.json").is_file()
    finally:
        writer.close()
    recovered = runner.recover_readiness_observations(writer.namespace, expected_head=HEAD)
    assert recovered["confirmed_slots"] == list(range(8))
    assert recovered["evidence_scope"] == "SYNTHETIC"


@pytest.mark.parametrize("committed", [0, 1, 4, 8])
def test_real_process_exit_restores_only_confirmed_slots(tmp_path, committed):
    namespace = tmp_path / "raw"
    code = '''import os, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import run_ig_predemo_readiness_2238 as r
w = r.ReadinessObservationWriter(Path(sys.argv[1]), head="a"*40, evidence_scope="SYNTHETIC")
w.start()
for i in range(int(sys.argv[2])):
    row = r._initial_readiness_rows()[i]
    row.update(status="PASS", reason_code="NONE")
    w.record(i, row)
os._exit(17)
'''
    run = subprocess.run([sys.executable, "-c", code, str(namespace), str(committed)], cwd=ROOT)
    assert run.returncode == 17
    recovered = runner.recover_readiness_observations(namespace, expected_head=HEAD)
    assert recovered["confirmed_slots"] == list(range(committed))
    rows = recovered["authenticated_read_matrix"]["resources"]
    assert [r["status"] for r in rows] == ["PASS"] * committed + ["UNKNOWN"] * (8-committed)
    assert recovered["evidence_scope"] == "SYNTHETIC"
    assert recovered["order_execution_enabled"] is False
    retry = runner.ReadinessObservationWriter(namespace, head=HEAD, evidence_scope="SYNTHETIC")
    with pytest.raises(FileExistsError):
        retry.start()


@pytest.mark.parametrize("fault", ["missing", "torn", "nan", "hash", "schema", "head", "namespace"])
def test_recovery_rejects_corrupt_committed_evidence(tmp_path, fault):
    namespace = tmp_path / "raw"
    writer = runner.ReadinessObservationWriter(namespace, head=HEAD, evidence_scope="SYNTHETIC")
    writer.start()
    writer.record(0, runner._initial_readiness_rows()[0])
    writer.close()
    path = namespace / "00.json"
    if fault == "missing":
        path.unlink()
    elif fault == "torn":
        path.write_text('{"row":')
    elif fault == "nan":
        path.write_text('{"row": NaN}')
    elif fault == "hash":
        (namespace / "00.receipt.json").write_text('{}')
    else:
        header = json.loads((namespace / "MANIFEST.json").read_text())
        header[{"schema":"schema", "head":"exact_head", "namespace":"namespace_fingerprint"}[fault]] = "wrong"
        (namespace / "MANIFEST.json").write_text(json.dumps(header))
    with pytest.raises((ValueError, OSError)):
        runner.recover_readiness_observations(namespace, expected_head=HEAD)


def test_disk_failure_preserves_all_reads_and_reports_persistence_separately(tmp_path, monkeypatch):
    writer = runner.ReadinessObservationWriter(tmp_path / "raw", head=HEAD, evidence_scope="SYNTHETIC")
    writer.start()
    client = MatrixClient()
    monkeypatch.setattr(runner, "atomic_write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    try:
        evidence = finalized(client, writer)
    finally:
        writer.close()
    assert len(client.calls) == 8
    assert evidence["authenticated_read_matrix"]["counts"]["PASS"] == 8
    assert evidence["raw_persistence"]["status"] == "BLOCKED"
    assert evidence["raw_persistence"]["confirmed_slots"] == []


def test_login_context_unknown_nested_keys_are_never_published():
    client = MatrixClient()
    client._login_context["unknown"] = [{"PaSsWoRd": "sentinel"}]
    evidence = finalized(client)
    assert "sentinel" not in json.dumps(evidence)
    assert "unknown" not in evidence["account"]


def test_second_process_cannot_read_while_writer_owns_cycle(tmp_path):
    namespace = tmp_path / "raw"
    writer = runner.ReadinessObservationWriter(namespace, head=HEAD, evidence_scope="SYNTHETIC")
    writer.start()
    try:
        code = '''import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import run_ig_predemo_readiness_2238 as r
try:
    r.recover_readiness_observations(Path(sys.argv[1]), expected_head="a"*40)
except RuntimeError:
    raise SystemExit(23)
'''
        result = subprocess.run([sys.executable, "-c", code, str(namespace)], cwd=ROOT)
        assert result.returncode == 23
    finally:
        writer.close()


@pytest.mark.parametrize("fault", ["missing_receipt", "empty_hashlist"])
def test_sealed_set_requires_every_receipt_and_full_hashlist(tmp_path, fault):
    writer = runner.ReadinessObservationWriter(tmp_path / "raw", head=HEAD, evidence_scope="SYNTHETIC")
    writer.start()
    try:
        finalized(writer=writer)
    finally:
        writer.close()
    if fault == "missing_receipt":
        (writer.namespace / "07.receipt.json").unlink()
    else:
        (writer.namespace / "COMPLETE.json").write_text('{"files":{}}')
    with pytest.raises((ValueError, OSError)):
        runner.recover_readiness_observations(writer.namespace, expected_head=HEAD)


@pytest.mark.parametrize("fault", ["none", "bad_receipt", "missing_readback", "wrong_target", "raise"])
def test_synthetic_transfer_requires_allowlisted_target_receipt_and_full_readback(tmp_path, fault):
    from hashlib import sha256

    calls = []
    def sink(files):
        calls.append(1)
        if fault == "raise":
            raise OSError("synthetic unavailable")
        result = {
            "target": "SYNTHETIC_ACCEPTANCE",
            "receipt": {name: sha256(data).hexdigest() for name, data in files.items()},
            "readback": dict(files),
        }
        if fault == "bad_receipt":
            result["receipt"]["READINESS.json"] = "0" * 64
        elif fault == "missing_readback":
            result["readback"].pop("MANIFEST.json")
        elif fault == "wrong_target":
            result["target"] = "UNAPPROVED"
        return result
    namespace = tmp_path / "derived"
    evidence = finalized()
    if fault == "none":
        runner._publish(namespace, evidence, {}, head=HEAD, synthetic_sink=sink)
    else:
        with pytest.raises(OSError):
            runner._publish(namespace, evidence, {}, head=HEAD, synthetic_sink=sink)
    assert calls == [1]
    assert json.loads((namespace / "READINESS.json").read_text()) == evidence
    with pytest.raises(FileExistsError):
        runner._publish(namespace, evidence, {}, head=HEAD, synthetic_sink=sink)
    assert calls == [1]
