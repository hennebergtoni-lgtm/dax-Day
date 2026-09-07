"""Verified loader for the exact frozen legacy V11.2 engine sources."""

from __future__ import annotations

import base64
import gzip
import hashlib
import sys
from types import ModuleType

from daxlab.reference.legacy_payload.candidate_00 import CHUNK as C00
from daxlab.reference.legacy_payload.candidate_01 import CHUNK as C01
from daxlab.reference.legacy_payload.candidate_02 import CHUNK as C02
from daxlab.reference.legacy_payload.candidate_03 import CHUNK as C03
from daxlab.reference.legacy_payload.candidate_04 import CHUNK as C04
from daxlab.reference.legacy_payload.oracle_00 import CHUNK as O00
from daxlab.reference.legacy_payload.oracle_01 import CHUNK as O01
from daxlab.reference.legacy_payload.oracle_02 import CHUNK as O02
from daxlab.reference.legacy_payload.oracle_03 import CHUNK as O03

ORACLE_SHA256 = "62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f"
CANDIDATE_SHA256 = "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"

ORACLE_GZIP_B64 = O00 + O01 + O02 + O03
CANDIDATE_GZIP_B64 = C00 + C01 + C02 + C03 + C04


def _decode(payload: str, expected_sha256: str) -> bytes:
    source = gzip.decompress(base64.b64decode(payload))
    actual = hashlib.sha256(source).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(f"Frozen legacy engine hash mismatch: {actual}")
    return source


def oracle_source_bytes() -> bytes:
    return _decode(ORACLE_GZIP_B64, ORACLE_SHA256)


def candidate_source_bytes() -> bytes:
    return _decode(CANDIDATE_GZIP_B64, CANDIDATE_SHA256)


def verify_legacy_sources() -> None:
    oracle_source_bytes()
    candidate_source_bytes()


def _load(source: bytes, module_name: str) -> ModuleType:
    module = ModuleType(module_name)
    module.__file__ = f"<frozen:{module_name}>"
    module.__package__ = module_name.rpartition(".")[0]
    sys.modules[module_name] = module
    # Source is cryptographically gated immediately above; execution is intentional.
    exec(compile(source, module.__file__, "exec"), module.__dict__)  # noqa: S102
    return module


def load_oracle() -> ModuleType:
    return _load(oracle_source_bytes(), "daxlab._legacy_oracle_v11_2")


def load_candidate() -> ModuleType:
    return _load(candidate_source_bytes(), "daxlab._legacy_candidate_v3_5_4_fix2")
