"""Load the exact recovered V11.2 engine payloads from repository artifacts."""

from __future__ import annotations

import base64
import hashlib
import sys
import types
import zlib
from pathlib import Path

from daxlab.reference.legacy_artifacts import (
    EXACT_ENGINE_EMBEDDED_SHA256,
    ORACLE_ENGINE_SHA256,
)

_ARTIFACT_DIR = Path(__file__).with_name("artifacts")


def _read_verified_source(filename: str, expected_sha256: str) -> str:
    encoded = (_ARTIFACT_DIR / filename).read_text(encoding="ascii").strip()
    source_bytes = zlib.decompress(base64.b64decode(encoded))
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(
            f"Recovered engine hash mismatch: expected {expected_sha256}, got {actual}"
        )
    return source_bytes.decode("utf-8")


def _load_module(module_name: str, source: str) -> types.ModuleType:
    module = types.ModuleType(module_name)
    module.__file__ = f"<recovered:{module_name}>"
    module.__package__ = ""
    sys.modules[module_name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def load_oracle_engine() -> types.ModuleType:
    """Load the frozen V11.2 oracle source after strict SHA verification."""
    source = _read_verified_source("oracle_v11_2.py.zlib.b64", ORACLE_ENGINE_SHA256)
    return _load_module("daxlab_v11_2_oracle_recovered", source)


def load_exact_candidate_engine() -> types.ModuleType:
    """Load the V3.5.4 exact-parity candidate after strict SHA verification."""
    source = _read_verified_source(
        "exact_candidate_v11_2.py.zlib.b64", EXACT_ENGINE_EMBEDDED_SHA256
    )
    return _load_module("daxlab_v11_2_exact_candidate_recovered", source)
