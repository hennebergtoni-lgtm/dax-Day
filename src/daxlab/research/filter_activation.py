from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


ACTIVATED = "ACTIVATED"
NO_OBSERVED_ACTIVATION = "NO_OBSERVED_ACTIVATION"
NON_MONOTONIC_GATE_BEHAVIOR = "NON_MONOTONIC_GATE_BEHAVIOR"


@dataclass(frozen=True)
class FilterActivationEvidence:
    filter_id: str
    observations: int
    changed_decisions: int
    newly_blocked: int
    newly_allowed: int
    status: str
    activation_ratio: float
    evidence_sha256: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_FILTER_ACTIVATION_EVIDENCE_V1",
            "filter_id": self.filter_id,
            "observations": self.observations,
            "changed_decisions": self.changed_decisions,
            "newly_blocked": self.newly_blocked,
            "newly_allowed": self.newly_allowed,
            "status": self.status,
            "activation_ratio": self.activation_ratio,
            "effectiveness_conclusion_allowed": self.status == ACTIVATED,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
            "evidence_sha256": self.evidence_sha256,
        }


def evaluate_filter_activation(
    off_keep_mask: Sequence[bool],
    on_keep_mask: Sequence[bool],
    *,
    filter_id: str,
) -> FilterActivationEvidence:
    """Verify that enabling a gate actually changes the tested decision path.

    For a pure restrictive filter, ON should be a subset of OFF. If enabling the
    candidate allows decisions that OFF rejected, the behavior is flagged as
    non-monotonic rather than silently treated as a normal filter ablation.
    """
    label = filter_id.strip()
    if not label:
        raise ValueError("filter_id must be non-empty")
    off = np.asarray(tuple(bool(value) for value in off_keep_mask), dtype=bool)
    on = np.asarray(tuple(bool(value) for value in on_keep_mask), dtype=bool)
    if off.ndim != 1 or off.size < 1:
        raise ValueError("off_keep_mask must contain at least one observation")
    if on.shape != off.shape:
        raise ValueError("ON/OFF decision vectors must have identical shape")

    changed = off != on
    newly_blocked = np.logical_and(off, ~on)
    newly_allowed = np.logical_and(~off, on)
    changed_count = int(np.count_nonzero(changed))
    blocked_count = int(np.count_nonzero(newly_blocked))
    allowed_count = int(np.count_nonzero(newly_allowed))
    if allowed_count:
        status = NON_MONOTONIC_GATE_BEHAVIOR
    elif changed_count == 0:
        status = NO_OBSERVED_ACTIVATION
    else:
        status = ACTIVATED

    identity = {
        "schema_version": "DAXLAB_FILTER_ACTIVATION_EVIDENCE_V1",
        "filter_id": label,
        "off_keep_mask": [bool(value) for value in off],
        "on_keep_mask": [bool(value) for value in on],
        "changed_decisions": changed_count,
        "newly_blocked": blocked_count,
        "newly_allowed": allowed_count,
        "status": status,
    }
    evidence_sha256 = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return FilterActivationEvidence(
        filter_id=label,
        observations=int(off.size),
        changed_decisions=changed_count,
        newly_blocked=blocked_count,
        newly_allowed=allowed_count,
        status=status,
        activation_ratio=float(changed_count / off.size),
        evidence_sha256=evidence_sha256,
    )
