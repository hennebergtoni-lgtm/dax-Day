"""Canonical local-file shape for IG Demo credentials.

This module has no network behavior and never renders credential values.  It is
shared by host preflight and the existing read-only IG payload so their accepted
key contract cannot drift.
"""
from __future__ import annotations

from pathlib import Path


REQUIRED_CREDENTIAL_KEYS = frozenset({"IG_USERNAME", "IG_PASSWORD", "IG_API_KEY"})


def load_ig_demo_credential_values(path: Path) -> dict[str, str]:
    """Load an exact three-key credential file without accepting extra fields."""
    if not path.is_file():
        raise RuntimeError("credentials file not found")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError("credentials file contains malformed line")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key in values:
            raise RuntimeError("duplicate credentials key")
        values[key] = value
    if REQUIRED_CREDENTIAL_KEYS - values.keys():
        raise RuntimeError("credentials file missing required keys")
    if values.keys() - REQUIRED_CREDENTIAL_KEYS:
        raise RuntimeError("credentials file contains unexpected keys")
    if any(not values[key] for key in REQUIRED_CREDENTIAL_KEYS):
        raise RuntimeError("credentials file contains empty value")
    return values
