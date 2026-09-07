"""Audit and fingerprint a recovered V11.2 M5 daily CSV directory."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from daxlab.data.legacy_dataset import audit_and_fingerprint_m5


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("m5_directory", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = audit_and_fingerprint_m5(args.m5_directory)
    payload = asdict(report)
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
