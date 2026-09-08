"""Persistent recovery-bundle contract for material replay/research runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from daxlab.runtime.checkpoint import ReplayCheckpoint
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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
        if status not in {"IN_PROGRESS", "COMPLETED", "ABORTED"}:
            raise ValueError("invalid recovery bundle status")
        checkpoint_payload = _canonical_json(asdict(checkpoint))
        return cls(
            schema_version="DAXLAB_RECOVERY_BUNDLE_V1",
            source_commit_sha=source_commit_sha,
            run_manifest_fingerprint=run_manifest.manifest_fingerprint,
            checkpoint_fingerprint=_sha256_text(checkpoint_payload),
            decision_log_fingerprint=decision_log.decision_ids_fingerprint,
            status=status,
        )


def write_recovery_bundle(
    directory: Path,
    *,
    bundle: RecoveryBundleManifest,
    run_manifest: RunManifest,
    checkpoint: ReplayCheckpoint,
    decision_log: DecisionLogManifest,
) -> dict[str, str]:
    """Write an atomic-ish, hash-addressed recovery surface to a durable directory."""
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
    if not checksums.exists():
        raise RuntimeError("recovery bundle checksums missing")
    for line in checksums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        target = directory / name
        if not target.exists():
            raise RuntimeError(f"recovery bundle file missing: {name}")
        observed = sha256(target.read_bytes()).hexdigest()
        if observed != digest:
            raise RuntimeError(f"recovery bundle hash mismatch: {name}")
