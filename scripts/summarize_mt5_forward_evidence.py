#!/usr/bin/env python3
"""Read-only summary of bounded MT5 SHADOW heartbeat history."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from daxlab.runtime.atomic_json import atomic_write_json
from daxlab.runtime.mt5_forward_evidence_summary import summarize_forward_evidence
from daxlab.runtime.mt5_heartbeat_history import load_heartbeat_history


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".runtime/mt5_shadow")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    state_dir = Path(args.state_dir).resolve()
    history_dir = state_dir / "heartbeat_history"
    heartbeats = load_heartbeat_history(history_dir)
    summary = summarize_forward_evidence(heartbeats)
    payload = asdict(summary)

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.output:
        atomic_write_json(Path(args.output).resolve(), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
