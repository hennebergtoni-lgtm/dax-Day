from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import NormalDist

_EULER_GAMMA = 0.5772156649015329
_NORMAL = NormalDist()
_NATIVE_UNIT = "NATIVE_PERIOD"


@dataclass(frozen=True)
class ClassicalDSRResult:
    probability: float
    z_score: float
    observed_sr: float
    benchmark_sr: float
    sr_star: float
    expected_max_z: float
    n_obs: int
    n_trials: int
    skewness: float
    pearson_kurtosis: float
    trial_sharpe_variance: float
    trial_variance_ddof: int
    sharpe_unit: str

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_CLASSICAL_DSR_V1",
            "method": "BAILEY_LOPEZ_DE_PRADO_CLASSICAL_DSR",
            "probability": self.probability,
            "z_score": self.z_score,
            "observed_sr": self.observed_sr,
            "benchmark_sr": self.benchmark_sr,
            "sr_star": self.sr_star,
            "expected_max_z": self.expected_max_z,
            "n_obs": self.n_obs,
            "n_trials": self.n_trials,
            "skewness": self.skewness,
            "pearson_kurtosis": self.pearson_kurtosis,
            "trial_sharpe_variance": self.trial_sharpe_variance,
            "trial_variance_ddof": self.trial_variance_ddof,
            "sharpe_unit": self.sharpe_unit,
            "autocorrelation_adjustment": False,
            "effective_trial_adjustment": False,
        }


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def expected_max_standard_normal(n_trials: int) -> float:
    """Classical extreme-value approximation E[max Z] for n independent trials."""
    if isinstance(n_trials, bool) or not isinstance(n_trials, int):
        raise TypeError("n_trials must be an integer")
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1")
    if n_trials == 1:
        return 0.0
    first = _NORMAL.inv_cdf(1.0 - 1.0 / n_trials)
    second = _NORMAL.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    return (1.0 - _EULER_GAMMA) * first + _EULER_GAMMA * second


def probabilistic_sharpe_ratio_from_statistics(
    *,
    observed_sr: float,
    benchmark_sr: float,
    n_obs: int,
    skewness: float,
    pearson_kurtosis: float,
) -> tuple[float, float]:
    """Return ``(probability, z_score)`` using the classical PSR formula."""
    observed = _finite(observed_sr, "observed_sr")
    benchmark = _finite(benchmark_sr, "benchmark_sr")
    skew = _finite(skewness, "skewness")
    kurt = _finite(pearson_kurtosis, "pearson_kurtosis")
    if isinstance(n_obs, bool) or not isinstance(n_obs, int):
        raise TypeError("n_obs must be an integer")
    if n_obs < 2:
        raise ValueError("n_obs must be >= 2")

    denominator_sq = 1.0 - skew * observed + ((kurt - 1.0) / 4.0) * observed**2
    if not math.isfinite(denominator_sq) or denominator_sq <= 0.0:
        raise ValueError("PSR denominator must be finite and > 0")
    z_score = (observed - benchmark) * math.sqrt(n_obs - 1) / math.sqrt(denominator_sq)
    probability = _NORMAL.cdf(z_score)
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("PSR probability is invalid")
    return probability, z_score


def classical_deflated_sharpe_ratio_from_statistics(
    *,
    observed_sr: float,
    n_obs: int,
    skewness: float,
    pearson_kurtosis: float,
    n_trials: int,
    trial_sharpe_variance: float,
    trial_variance_ddof: int,
    benchmark_sr: float = 0.0,
    sharpe_unit: str = _NATIVE_UNIT,
) -> ClassicalDSRResult:
    """Compute classical DSR from explicit native-frequency summary statistics.

    The caller owns estimation of the cross-trial Sharpe variance. ``ddof`` is
    recorded for provenance but is not silently transformed here.
    """
    if sharpe_unit != _NATIVE_UNIT:
        raise ValueError("sharpe_unit must be NATIVE_PERIOD; convert annualized Sharpe explicitly")
    if trial_variance_ddof not in (0, 1) or isinstance(trial_variance_ddof, bool):
        raise ValueError("trial_variance_ddof must be 0 or 1")
    variance = _finite(trial_sharpe_variance, "trial_sharpe_variance")
    if variance < 0.0:
        raise ValueError("trial_sharpe_variance must be >= 0")

    expected_max_z = expected_max_standard_normal(n_trials)
    base_benchmark = _finite(benchmark_sr, "benchmark_sr")
    sr_star = base_benchmark + math.sqrt(variance) * expected_max_z
    probability, z_score = probabilistic_sharpe_ratio_from_statistics(
        observed_sr=observed_sr,
        benchmark_sr=sr_star,
        n_obs=n_obs,
        skewness=skewness,
        pearson_kurtosis=pearson_kurtosis,
    )
    return ClassicalDSRResult(
        probability=probability,
        z_score=z_score,
        observed_sr=float(observed_sr),
        benchmark_sr=base_benchmark,
        sr_star=sr_star,
        expected_max_z=expected_max_z,
        n_obs=n_obs,
        n_trials=n_trials,
        skewness=float(skewness),
        pearson_kurtosis=float(pearson_kurtosis),
        trial_sharpe_variance=variance,
        trial_variance_ddof=trial_variance_ddof,
        sharpe_unit=sharpe_unit,
    )
