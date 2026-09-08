"""Persistent recovery bundle contract for material DAX research/replay runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from daxlab.runtime.checkpoint import ReplayCheckpoint
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest


@dataclass(frozen=True, slots=True)
class RecoveryBundleManifest:
    schema_version: str
    source_commit_sha: str
    run_manifest_fingerprint: str
    dataset_fingerprint: str
    engine_fingerprint: str
    config_fingerprint: str
    mode: str
    status: str
    files: dict[str, str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def write_recovery_bundle(
    directory: str | Path,
    *,
    run_manifest: RunManifest,
    decision_log: DecisionLogManifest,
    checkpoint: ReplayCheckpoint | None,
    source_commit_sha: str,
    status: str,
    result_payload: dict[str, Any] | None = None,
) -> RecoveryBundleManifest:
    """Persist enough provenance to reconstruct or safely reject a material run."""
    if status not in {"RUNNING", "COMPLETED", "ABORTED"}:
        raise ValueError("invalid recovery status")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    run_path = root / "run_manifest.json"
    log_path = root / "decision_log_manifest.json"
    _write_json(run_path, asdict(run_manifest))
    _write_json(log_path, asdict(decision_log))

    paths = [run_path, log_path]
    if checkpoint is not None:
        checkpoint_path = root / "checkpoint.json"
        _write_json(checkpoint_path, asdict(checkpoint))
        paths.append(checkpoint_path)
    if result_payload is not None:
        result_path = root / "result.json"
        _write_json(result_path, result_payload)
        paths.append(result_path)

    files = {path.name: _sha256(path) for path in paths}
    manifest = RecoveryBundleManifest(
        schema_version="DAXLAB_RECOVERY_BUNDLE_V1",
        source_commit_sha=source_commit_sha,
        run_manifest_fingerprint=run_manifest.manifest_fingerprint,
        dataset_fingerprint=run_manifest.dataset_fingerprint,
        engine_fingerprint=run_manifest.engine_fingerprint,
        config_fingerprint=run_manifest.config_fingerprint,
        mode=run_manifest.mode.value,
        status=status,
        files=files,
    )
    _write_json(root / "recovery_bundle_manifest.json", asdict(manifest))
    return manifest


def verify_recovery_bundle(directory: str | Path) -> RecoveryBundleManifest:
    """Fail closed if a persisted recovery file is missing or changed."""
    root = Path(directory)
    payload = json.loads((root / "recovery_bundle_manifest.json").read_text(encoding="utf-8"))
    manifest = RecoveryBundleManifest(**payload)
    if manifest.schema_version != "DAXLAB_RECOVERY_BUNDLE_V1":
        raise RuntimeError("unsupported recovery bundle schema")
    for name, expected in manifest.files.items():
        path = root / name
        if not path.is_file():
            raise RuntimeError(f"recovery bundle missing file: {name}")
        if _sha256(path) != expected:
            raise RuntimeError(f"recovery bundle hash mismatch: {name}")
    return manifest
