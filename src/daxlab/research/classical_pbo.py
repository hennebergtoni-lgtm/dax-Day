from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ClassicalPBOResult:
    pbo: float
    logits: tuple[float, ...]
    n_combinations: int
    n_trials: int
    n_periods: int
    n_splits: int
    performance_metric: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_CLASSICAL_PBO_V1",
            "method": "CSCV_CLASSICAL_PBO",
            "pbo": self.pbo,
            "logits": list(self.logits),
            "n_combinations": self.n_combinations,
            "n_trials": self.n_trials,
            "n_periods": self.n_periods,
            "n_splits": self.n_splits,
            "performance_metric": self.performance_metric,
            "purge_enabled": False,
            "embargo_enabled": False,
        }


def _validate_matrix(returns: Iterable[Iterable[float]]) -> np.ndarray:
    matrix = np.asarray(returns, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("returns must be a 2-D matrix shaped n_trials x n_periods")
    n_trials, n_periods = matrix.shape
    if n_trials < 2:
        raise ValueError("returns must contain at least 2 trials")
    if n_periods < 2:
        raise ValueError("returns must contain at least 2 periods")
    if not np.isfinite(matrix).all():
        raise ValueError("returns must contain only finite values")
    return matrix


def _sample_sharpe(values: np.ndarray) -> float:
    if values.ndim != 1 or values.size < 2:
        raise ValueError("each CSCV slice must contain at least 2 periods")
    spread = float(np.ptp(values))
    if spread == 0.0:
        return 0.0
    std = float(values.std(ddof=1))
    if not math.isfinite(std) or std <= 0.0:
        return 0.0
    score = float(values.mean() / std)
    if not math.isfinite(score):
        raise ValueError("performance metric produced a non-finite value")
    return score


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        average_rank = ((i + 1) + j) / 2.0
        ranks[order[i:j]] = average_rank
        i = j
    return ranks


def _contiguous_blocks(n_periods: int, n_splits: int) -> tuple[np.ndarray, ...]:
    base, remainder = divmod(n_periods, n_splits)
    blocks: list[np.ndarray] = []
    cursor = 0
    for idx in range(n_splits):
        size = base + (1 if idx < remainder else 0)
        blocks.append(np.arange(cursor, cursor + size, dtype=int))
        cursor += size
    return tuple(blocks)


def classical_probability_of_backtest_overfitting(
    returns: Iterable[Iterable[float]], *, n_splits: int = 16
) -> ClassicalPBOResult:
    """Estimate classical PBO via combinatorially symmetric cross-validation.

    ``returns`` must be shaped ``n_trials x n_periods`` on one shared,
    chronologically ordered time axis. This V1 intentionally does not purge or
    embargo boundaries; those require separate time/horizon evidence.
    """
    matrix = _validate_matrix(returns)
    if isinstance(n_splits, bool) or not isinstance(n_splits, int):
        raise TypeError("n_splits must be an integer")
    if n_splits < 2 or n_splits % 2 != 0:
        raise ValueError("n_splits must be an even integer >= 2")
    n_trials, n_periods = matrix.shape
    if n_periods < n_splits:
        raise ValueError("n_periods must be >= n_splits")

    blocks = _contiguous_blocks(n_periods, n_splits)
    if any(len(block) == 0 for block in blocks):
        raise ValueError("each contiguous block must be non-empty")

    all_block_ids = tuple(range(n_splits))
    logits: list[float] = []
    for is_block_ids in combinations(all_block_ids, n_splits // 2):
        is_set = set(is_block_ids)
        oos_block_ids = tuple(idx for idx in all_block_ids if idx not in is_set)
        is_idx = np.concatenate([blocks[idx] for idx in is_block_ids])
        oos_idx = np.concatenate([blocks[idx] for idx in oos_block_ids])
        if is_idx.size < 2 or oos_idx.size < 2:
            raise ValueError("each CSCV half must contain at least 2 periods")

        is_scores = np.asarray([_sample_sharpe(matrix[row, is_idx]) for row in range(n_trials)])
        oos_scores = np.asarray([_sample_sharpe(matrix[row, oos_idx]) for row in range(n_trials)])
        best_trial = int(np.argmax(is_scores))
        ranks = _average_ranks(oos_scores)
        omega = float(ranks[best_trial] / (n_trials + 1.0))
        logit = math.log(omega / (1.0 - omega))
        logits.append(logit)

    if not logits:
        raise ValueError("CSCV produced no combinations")
    pbo = sum(value < 0.0 for value in logits) / len(logits)
    return ClassicalPBOResult(
        pbo=float(pbo),
        logits=tuple(float(value) for value in logits),
        n_combinations=len(logits),
        n_trials=n_trials,
        n_periods=n_periods,
        n_splits=n_splits,
        performance_metric="SAMPLE_SHARPE_DDOF1",
    )
