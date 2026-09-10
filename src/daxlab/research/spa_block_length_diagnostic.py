from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
import math
from typing import Sequence

import numpy as np

from daxlab.research.pbo_evidence_adapter import PBOEvidenceMatrix


@dataclass(frozen=True)
class SPABlockLengthDiagnostic:
    model_stationary_block_lengths: tuple[float, ...]
    stationary_min: float
    stationary_median: float
    stationary_max: float
    n_models: int
    n_periods: int
    arch_version: str
    method: str
    matrix_sha256: str
    upstream_evidence_sha256: str
    benchmark_returns: tuple[float, ...]
    diagnostic_sha256: str
    selected_block_size: int | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_SPA_BLOCK_LENGTH_DIAGNOSTIC_V1",
            "method": self.method,
            "arch_version": self.arch_version,
            "model_stationary_block_lengths": list(self.model_stationary_block_lengths),
            "stationary_min": self.stationary_min,
            "stationary_median": self.stationary_median,
            "stationary_max": self.stationary_max,
            "n_models": self.n_models,
            "n_periods": self.n_periods,
            "matrix_sha256": self.matrix_sha256,
            "upstream_evidence_sha256": self.upstream_evidence_sha256,
            "benchmark_returns": list(self.benchmark_returns),
            "diagnostic_sha256": self.diagnostic_sha256,
            "selected_block_size": self.selected_block_size,
            "automatic_selection_applied": False,
            "spa_computed": False,
            "confirmatory_use_allowed": False,
        }


def diagnose_spa_stationary_block_lengths(
    evidence: PBOEvidenceMatrix,
    *,
    benchmark_returns: Sequence[float],
) -> SPABlockLengthDiagnostic:
    """Estimate per-model stationary-bootstrap block lengths using arch.

    Uses Politis-White (2004), with the Patton-Politis-White (2009) correction,
    as implemented by ``arch.bootstrap.optimal_block_length``. No single common
    block size is selected here.
    """
    matrix = np.asarray(evidence.matrix, dtype=float)
    benchmark = np.asarray(tuple(float(value) for value in benchmark_returns), dtype=float)
    if matrix.ndim != 2:
        raise ValueError("model return matrix must be 2D")
    n_models, n_periods = map(int, matrix.shape)
    if n_models < 1 or n_periods < 3:
        raise ValueError("at least one model and three periods are required")
    if benchmark.shape != (n_periods,):
        raise ValueError("benchmark return length must match period count")
    if not np.isfinite(matrix).all() or not np.isfinite(benchmark).all():
        raise ValueError("model and benchmark returns must be finite")

    # arch.SPA uses loss_diff = benchmark_loss - model_loss. Since DAXLAB
    # defines loss = -return, this equals model_return - benchmark_return.
    loss_differentials = matrix.T - benchmark[:, None]

    try:
        from arch.bootstrap import optimal_block_length
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install the project with the 'statistics' extra") from exc

    estimates = optimal_block_length(loss_differentials)
    if "stationary" not in estimates.columns or len(estimates) != n_models:
        raise RuntimeError("arch optimal_block_length returned an unexpected schema")
    stationary = np.asarray(estimates["stationary"], dtype=float)
    if stationary.shape != (n_models,) or not np.isfinite(stationary).all():
        raise RuntimeError("arch returned invalid stationary block-length estimates")
    if np.any(stationary < 1.0):
        raise RuntimeError("arch returned a stationary block length below one")

    values = tuple(float(value) for value in stationary)
    stationary_min = float(np.min(stationary))
    stationary_median = float(np.median(stationary))
    stationary_max = float(np.max(stationary))
    if not all(math.isfinite(value) for value in (stationary_min, stationary_median, stationary_max)):
        raise RuntimeError("block-length summary is non-finite")

    arch_version = version("arch")
    method = "ARCH_POLITIS_WHITE_PATTON_OPTIMAL_STATIONARY_BLOCK_LENGTH"
    benchmark_tuple = tuple(float(value) for value in benchmark)
    identity = {
        "schema_version": "DAXLAB_SPA_BLOCK_LENGTH_DIAGNOSTIC_V1",
        "method": method,
        "arch_version": arch_version,
        "model_stationary_block_lengths": list(values),
        "stationary_min": stationary_min,
        "stationary_median": stationary_median,
        "stationary_max": stationary_max,
        "n_models": n_models,
        "n_periods": n_periods,
        "matrix_sha256": evidence.matrix_sha256,
        "upstream_evidence_sha256": evidence.upstream_evidence_sha256,
        "benchmark_returns": list(benchmark_tuple),
        "selected_block_size": None,
        "automatic_selection_applied": False,
        "spa_computed": False,
        "confirmatory_use_allowed": False,
    }
    diagnostic_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return SPABlockLengthDiagnostic(
        model_stationary_block_lengths=values,
        stationary_min=stationary_min,
        stationary_median=stationary_median,
        stationary_max=stationary_max,
        n_models=n_models,
        n_periods=n_periods,
        arch_version=arch_version,
        method=method,
        matrix_sha256=evidence.matrix_sha256,
        upstream_evidence_sha256=evidence.upstream_evidence_sha256,
        benchmark_returns=benchmark_tuple,
        diagnostic_sha256=diagnostic_sha256,
        selected_block_size=None,
    )
