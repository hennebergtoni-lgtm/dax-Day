from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import NormalDist


_NORMAL = NormalDist()


@dataclass(frozen=True)
class ClassicalMinTRLResult:
    status: str
    min_track_record_length: float
    required_observations: float
    observed_sr: float
    benchmark_sr: float
    skewness: float
    pearson_kurtosis: float
    confidence: float
    sharpe_unit: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_CLASSICAL_MINTRL_V1",
            "method": "BAILEY_LOPEZ_DE_PRADO_CLASSICAL_MINTRL",
            "status": self.status,
            "min_track_record_length": self.min_track_record_length,
            "required_observations": self.required_observations,
            "observed_sr": self.observed_sr,
            "benchmark_sr": self.benchmark_sr,
            "skewness": self.skewness,
            "pearson_kurtosis": self.pearson_kurtosis,
            "confidence": self.confidence,
            "sharpe_unit": self.sharpe_unit,
            "annualized": False,
            "autocorrelation_adjustment": False,
        }


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def classical_minimum_track_record_length_from_statistics(
    *,
    observed_sr: float,
    benchmark_sr: float,
    skewness: float,
    pearson_kurtosis: float,
    confidence: float = 0.95,
    sharpe_unit: str = "NATIVE_PERIOD",
) -> ClassicalMinTRLResult:
    """Analytic inverse of the classical PSR sample-length relation."""
    if sharpe_unit != "NATIVE_PERIOD":
        raise ValueError("sharpe_unit must be NATIVE_PERIOD")
    observed = _finite(observed_sr, "observed_sr")
    benchmark = _finite(benchmark_sr, "benchmark_sr")
    skew = _finite(skewness, "skewness")
    kurt = _finite(pearson_kurtosis, "pearson_kurtosis")
    conf = _finite(confidence, "confidence")
    if not 0.5 < conf < 1.0:
        raise ValueError("confidence must be strictly between 0.5 and 1.0")

    denominator_sq = 1.0 - skew * observed + ((kurt - 1.0) / 4.0) * observed**2
    if not math.isfinite(denominator_sq) or denominator_sq <= 0.0:
        raise ValueError("PSR denominator must be finite and > 0")

    delta = observed - benchmark
    if delta <= 0.0:
        return ClassicalMinTRLResult(
            status="NEVER_SIGNIFICANT_AT_CURRENT_ESTIMATE",
            min_track_record_length=math.inf,
            required_observations=math.inf,
            observed_sr=observed,
            benchmark_sr=benchmark,
            skewness=skew,
            pearson_kurtosis=kurt,
            confidence=conf,
            sharpe_unit=sharpe_unit,
        )

    z_required = _NORMAL.inv_cdf(conf)
    min_length = 1.0 + denominator_sq * (z_required / delta) ** 2
    if not math.isfinite(min_length) or min_length <= 1.0:
        raise ValueError("computed MinTRL is invalid")
    required_observations = max(2, math.ceil(min_length))
    return ClassicalMinTRLResult(
        status="FINITE_REQUIREMENT",
        min_track_record_length=min_length,
        required_observations=float(required_observations),
        observed_sr=observed,
        benchmark_sr=benchmark,
        skewness=skew,
        pearson_kurtosis=kurt,
        confidence=conf,
        sharpe_unit=sharpe_unit,
    )
