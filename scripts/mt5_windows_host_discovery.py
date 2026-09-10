#!/usr/bin/env python3
"""Read-only Windows host discovery for the MT5 SHADOW runtime.

Prints a credential-free JSON object containing the current Python executable,
repository root, supervisor path, platform, and whether MetaTrader5 can be
imported. It performs no MT5 initialize/login and no Windows mutation.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import platform
import sys
from typing import Any


SCHEMA_VERSION = "DAXLAB_MT5_WINDOWS_HOST_DISCOVERY_V1"


def collect_host_discovery(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = (
        repo_root.expanduser().resolve()
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )
    supervisor = root / "scripts" / "mt5_shadow_supervisor.py"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_system": platform.system(),
        "python_exe": str(Path(sys.executable).resolve()),
        "repo_root": str(root),
        "supervisor_script": str(supervisor.resolve()),
        "supervisor_exists": supervisor.is_file(),
        "metatrader5_importable": importlib.util.find_spec("MetaTrader5") is not None,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "credentials_included": False,
    }
    return payload


def main() -> int:
    print(json.dumps(collect_host_discovery(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
