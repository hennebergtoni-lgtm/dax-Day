"""Persistent recovery-bundle contract for material replay/research runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from daxlab.runtime.checkpoint import ReplayCheckpoint, assert_resume_compatible
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.manifests import (
    DecisionLogManifest,
    RunManifest,
    assert_run_manifest_matches,
)


_SCHEMA = "DAXLAB_RECOVERY_BUNDLE_V1"
_STATUSES = frozenset({"IN_PROGRESS", "COMPLETED", "ABORTED"})
_PAYLOAD_FILES = frozenset({
    "bundle_manifest.json", "run_manifest.json", "checkpoint.json", "decision_log_manifest.json",
})


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    )


def _sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RecoveryBundleManifest:
    schema_version: str
    source_commit_sha: str
    run_manifest_fingerprint: str
    checkpoint_fingerprint: str
    decision_log_fingerprint: str
    status: str

    @classmethod
    def build(
        cls,
        *,
        source_commit_sha: str,
        run_manifest: RunManifest,
        checkpoint: ReplayCheckpoint,
        decision_log: DecisionLogManifest,
        status: str,
    ) -> RecoveryBundleManifest:
        if status not in _STATUSES:
            raise ValueError("invalid recovery bundle status")
        checkpoint_payload = _canonical_json(asdict(checkpoint))
        bundle = cls(
            schema_version=_SCHEMA,
            source_commit_sha=source_commit_sha,
            run_manifest_fingerprint=run_manifest.manifest_fingerprint,
            checkpoint_fingerprint=_sha256_text(checkpoint_payload),
            decision_log_fingerprint=decision_log.decision_ids_fingerprint,
            status=status,
        )
        _validate_surface(bundle, run_manifest, checkpoint, decision_log)
        return bundle


def _validate_surface(
    bundle: RecoveryBundleManifest,
    run: RunManifest,
    checkpoint: ReplayCheckpoint,
    log: DecisionLogManifest,
) -> None:
    """Validate the same provenance contract before writing and after hash verification."""
    if bundle.schema_version != _SCHEMA:
        raise ValueError("recovery bundle schema mismatch")
    if bundle.status not in _STATUSES:
        raise ValueError("invalid recovery bundle status")
    for value in (
        bundle.source_commit_sha, run.dataset_fingerprint, run.engine_fingerprint,
        run.config_fingerprint, run.manifest_fingerprint, log.decision_ids_fingerprint,
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("recovery identities must be non-empty strings")
    if not isinstance(run.mode, RuntimeMode):
        raise ValueError("invalid recovery run mode")
    run_identity = {
        "dataset_fingerprint": run.dataset_fingerprint,
        "engine_fingerprint": run.engine_fingerprint,
        "config_fingerprint": run.config_fingerprint,
        "mode": run.mode.value,
    }
    assert_run_manifest_matches(
        replace(run, manifest_fingerprint=stable_fingerprint(run_identity)), run,
    )
    assert_resume_compatible(checkpoint, run)
    if type(checkpoint.processed_candles) is not int or checkpoint.processed_candles < 0:
        raise ValueError("processed_candles must be a non-negative integer")
    if checkpoint.last_event_time_iso is not None and not isinstance(
        checkpoint.last_event_time_iso, str,
    ):
        raise ValueError("last_event_time_iso must be a string or null")
    for count in (log.decisions, log.trades, log.no_trades):
        if type(count) is not int or count < 0:
            raise ValueError("decision log counts must be non-negative integers")
    if log.decisions != log.trades + log.no_trades:
        raise ValueError("decision log counts are inconsistent")
    if checkpoint.decision_log_fingerprint != log.decision_ids_fingerprint:
        raise RuntimeError("recovery checkpoint decision-log mismatch")
    if bundle.run_manifest_fingerprint != run.manifest_fingerprint:
        raise RuntimeError("recovery bundle run-manifest mismatch")
    if bundle.checkpoint_fingerprint != _sha256_text(_canonical_json(asdict(checkpoint))):
        raise RuntimeError("recovery bundle checkpoint fingerprint mismatch")
    if bundle.decision_log_fingerprint != log.decision_ids_fingerprint:
        raise RuntimeError("recovery bundle decision-log mismatch")


def write_recovery_bundle(
    directory: Path,
    *,
    bundle: RecoveryBundleManifest,
    run_manifest: RunManifest,
    checkpoint: ReplayCheckpoint,
    decision_log: DecisionLogManifest,
) -> dict[str, str]:
    """Write an atomic-ish, hash-addressed recovery surface to a durable directory."""
    _validate_surface(bundle, run_manifest, checkpoint, decision_log)
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {
        "bundle_manifest.json": asdict(bundle),
        "run_manifest.json": asdict(run_manifest),
        "checkpoint.json": asdict(checkpoint),
        "decision_log_manifest.json": asdict(decision_log),
    }
    hashes: dict[str, str] = {}
    for name, payload in payloads.items():
        text = _canonical_json(payload) + "\n"
        tmp = directory / f".{name}.tmp"
        target = directory / name
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(target)
        hashes[name] = _sha256_text(text)
    checksum_text = "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items()))
    tmp_checksums = directory / ".SHA256SUMS.tmp"
    tmp_checksums.write_text(checksum_text, encoding="utf-8")
    tmp_checksums.replace(directory / "SHA256SUMS")
    return hashes


def verify_recovery_bundle(directory: Path) -> None:
    """Fail closed if a persisted recovery surface is incomplete or tampered with."""
    checksums = directory / "SHA256SUMS"
    if not checksums.is_file() or checksums.is_symlink():
        raise RuntimeError("recovery bundle checksums missing")
    entries: dict[str, str] = {}
    for line in checksums.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise RuntimeError("invalid recovery bundle checksum entry")
        digest, name = match.groups()
        if name not in _PAYLOAD_FILES or name in entries:
            raise RuntimeError("invalid or duplicate recovery bundle filename")
        entries[name] = digest
    if entries.keys() != _PAYLOAD_FILES:
        raise RuntimeError("recovery bundle checksum file list incomplete")
    payloads: dict[str, bytes] = {}
    for name, digest in entries.items():
        target = directory / name
        if not target.is_file() or target.is_symlink():
            raise RuntimeError(f"recovery bundle file missing: {name}")
        payload = target.read_bytes()
        observed = sha256(payload).hexdigest()
        if observed != digest:
            raise RuntimeError(f"recovery bundle hash mismatch: {name}")
        payloads[name] = payload
    try:
        bundle = RecoveryBundleManifest(**_read_object(payloads["bundle_manifest.json"]))
        run_fields = _read_object(payloads["run_manifest.json"])
        run_fields["mode"] = RuntimeMode(run_fields["mode"])
        run = RunManifest(**run_fields)
        checkpoint = ReplayCheckpoint(**_read_object(payloads["checkpoint.json"]))
        log = DecisionLogManifest(**_read_object(payloads["decision_log_manifest.json"]))
        _validate_surface(bundle, run, checkpoint, log)
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise RuntimeError(f"invalid recovery bundle payload: {exc}") from exc


def _read_object(payload: bytes) -> dict[str, Any]:
    def unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value: {value}")

    result = json.loads(
        payload, object_pairs_hook=unique_fields, parse_constant=reject_constant,
    )
    if not isinstance(result, dict):
        raise ValueError("recovery payload must be a JSON object")
    return result
