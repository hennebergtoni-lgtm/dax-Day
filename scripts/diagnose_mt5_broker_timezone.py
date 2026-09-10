#!/usr/bin/env python3
"""Read-only MT5 broker-timezone diagnostic CLI; never auto-verifies a timezone."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from daxlab.runtime.mt5_broker_timezone_diagnostic import diagnose_broker_timezone
from mt5_windows_probe import collect_probe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="DE40")
    parser.add_argument("--candidate", action="append", dest="candidates", required=True)
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=600.0)
    parser.add_argument("--output", default="mt5_broker_timezone_diagnostic.json")
    args = parser.parse_args()

    payload = diagnose_broker_timezone(
        probe=collect_probe,
        symbol=args.symbol,
        candidates=tuple(args.candidates),
        bars=args.bars,
        max_age_seconds=args.max_age_seconds,
    )
    path = Path(args.output)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence file: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"WROTE {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
