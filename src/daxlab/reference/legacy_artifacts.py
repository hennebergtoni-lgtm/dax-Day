"""Contracts for importing the proven Colab/Drive V11.2 research artifacts.

No private Drive identifiers are stored here. The public repository records only
stable artifact names, expected hashes, and relative legacy locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ArtifactExpectation:
    key: str
    filename: str
    expected_sha256: str | None = None
    legacy_relative_path: str | None = None
    required_for_gate: bool = True


EXACT_ENGINE = ArtifactExpectation(
    key="v11_2_exact_engine",
    filename="NEXT_ENGINE_V3_5_4_FIX2_EXACT_ENGINE_PARITY_GATE.ipynb",
    expected_sha256=(
        "9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887"
    ),
)

# Verified 2026-09-07 by extracting the embedded engine source from EXACT_ENGINE.
# This is the exact parity candidate source used by the proven V3.5.4 gate.
EXACT_ENGINE_EMBEDDED_SHA256 = (
    "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
)
EXACT_ENGINE_EMBEDDED_CHARS = 51501

# Verified 2026-09-07 by extracting the engine payload written by V11_2_ONE_CLICK.ipynb.
# This is the frozen oracle/reference source against which parity is judged.
ORACLE_ENGINE_SHA256 = "62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f"
ORACLE_ENGINE_CHARS = 35819

FAST_RUNNER = ArtifactExpectation(
    key="v2_8_18_fast_runner",
    filename="DAX_V11_2_V2_8_18_FAST_FULL_RESEARCH_ONE_CLICK.ipynb",
)

FULL_WF_SUMMARY = ArtifactExpectation(
    key="v11_2_full_wf_summary",
    filename="FULL_WF_SUMMARY.csv",
    legacy_relative_path="V11_2_FULL_WF_SESSION_DAY_V4_FIX1/FULL_WF_SUMMARY.csv",
)

LEGACY_CACHE_ROOT_NAME = "DAX_V14_RECOVERED_CACHE_V13"


def sha256_file(path: str | Path) -> str:
    source = Path(path)
    digest = sha256()
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_artifact(path: str | Path, expectation: ArtifactExpectation) -> str:
    """Verify filename and, when known, exact SHA-256 before migration."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.name != expectation.filename:
        raise ValueError(
            f"Wrong artifact for {expectation.key}: expected {expectation.filename}, "
            f"got {source.name}"
        )

    actual = sha256_file(source)
    if expectation.expected_sha256 is not None and actual != expectation.expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {expectation.key}: expected "
            f"{expectation.expected_sha256}, got {actual}"
        )
    return actual
