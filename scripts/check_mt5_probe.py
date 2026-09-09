"""Validate a credential-free Windows MT5 evidence bundle and print one status line."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from daxlab.runtime.mt5_windows_bundle import compact_status, parse_windows_mt5_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="mt5_probe.json")
    args = parser.parse_args()
    path = Path(args.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    bundle = parse_windows_mt5_bundle(payload)
    print(compact_status(bundle))
    if bundle.feed is not None:
        print(
            "FEED | "
            f"bars={len(bundle.feed.bars)} | "
            f"age_s={bundle.feed.age_seconds:.1f} | "
            f"fingerprint={bundle.feed.latest_closed_fingerprint[:12]}"
        )
    print(f"EVIDENCE_SHA256 | {bundle.fingerprint}")
    return 0 if bundle.green else 2


if __name__ == "__main__":
    raise SystemExit(main())
