"""Research registry: experiments are explicit records, never implicit notebook state."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from daxlab.contracts import ExperimentManifest


class ExperimentRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, experiment_id: str) -> Path:
        return self.root / experiment_id / "manifest.json"

    def save(self, manifest: ExperimentManifest) -> Path:
        path = self.path_for(manifest.experiment_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(manifest)
        payload["status"] = manifest.status.value
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path
