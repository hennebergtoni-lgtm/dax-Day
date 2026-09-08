"""Post-trade EXIT001 diagnostics. Never eligible for pre-entry decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExitDiagnostics:
    realized_r: float
    mfe_r: float
    mae_r: float
    capture_ratio: float | None
    adverse_to_realized_ratio: float | None


def describe_exit(*, realized_r: float, mfe_r: float, mae_r: float) -> ExitDiagnostics:
    """Describe realized/MFE/MAE relationships after a trade is complete."""
    if mfe_r < 0:
        raise ValueError("mfe_r must be non-negative")
    if mae_r > 0:
        raise ValueError("mae_r must be non-positive")
    capture = None if mfe_r == 0 else realized_r / mfe_r
    adverse = None if realized_r == 0 else abs(mae_r) / abs(realized_r)
    return ExitDiagnostics(
        realized_r=float(realized_r),
        mfe_r=float(mfe_r),
        mae_r=float(mae_r),
        capture_ratio=capture,
        adverse_to_realized_ratio=adverse,
    )
