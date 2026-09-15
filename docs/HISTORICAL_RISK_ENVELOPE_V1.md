# Historical Risk Envelope — descriptive read-only research

Owner reuse: `detail_artifact_loader.preflight_detail_csv` verifies exact artifact
bytes, expected count and typed deterministic detail rows; existing
`research.failure_analysis` now describes empirical distributions. No risk policy,
strategy, cost model or runtime admission changes. Reader is stdout-only:

```powershell
$env:PYTHONPATH = 'src'
python scripts/analyze_historical_risk_envelope.py
python scripts/analyze_historical_risk_envelope.py --trades <VERIFIED_TRADES_NORMAL_CSV>
```

Default observation in this checkout: **0 supplied verified detail rows**,
INSUFFICIENT_SAMPLE / WAITING_EXTERNAL_PINNED_TRADES_ARTIFACT. No MAE/MFE values are
available. The original 856-row clean-reference artifact must match committed
`reference/detail_artifacts.py`: SHA256
`f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023`.
Wrong bytes fail closed. The tool neither rebuilds missing data nor imports it.

For supplied canonical rows, the analyzer computes signed-source MAE magnitudes,
MFE, median/P90/P95/P99/worst observed, durations, Long/Short strata, within-WF /
selected-variant losing streaks, session/ISO-week net-R chains and trade-boundary
net-R drawdown distributions. Groups with overlapping trades have UNKNOWN loss
sequence/drawdown instead of a fictional sequential account. Cross-WF chains are
UNKNOWN. Source sign/time/hash/count/duplicate conflicts fail closed.

Empirical linear interpolation is a sample description, not a bound on future
tail losses. Each quantity reports its observation count. No reviewed minimum
sample or tail-confidence criterion exists here: inference and survival verdict
remain UNVERIFIED_THRESHOLD. No PASS/WARN/FAIL or risk promotion is generated.
Regime/Structure/Setup/OR5/OR15 joins require pinned selected-variant/causal evidence;
those absent splits stay UNKNOWN. Normal net-R alone cannot reveal gross-R or
per-trade cost stress. MAE/MFE cannot identify execution slippage or gap causality.

Existing **static V11.2 summary**, read from unchanged
`research/V112_REFERENCE_V1/reference_result.json`, is distinct from this tool's
missing detail source and from CAND-001 runtime/broker state:

| Existing cost scenario | OOS trades | Observed total net R |
| --- | ---: | ---: |
| normal | 856 | -31.309210619787684 |
| stress_1.5x | 856 | -40.921695023387514 |
| stress_2x | 856 | -48.424611963007294 |

These frozen aggregates do not supply per-trade excursion quantiles or a survival
PASS criterion. They are not rerun, reinterpreted as today's PnL, or refreshed.
Existing CAND-001 cost-integrity audit remains authoritative for its own causal
1.x stress contracts; it is not interchangeable with the V11.2 source.

Tests use explicitly synthetic fixtures solely to check quantile arithmetic,
source row integrity, chronology, duplicates, edge samples and unavailable fields.
No test output is classified as real historical or broker evidence.
