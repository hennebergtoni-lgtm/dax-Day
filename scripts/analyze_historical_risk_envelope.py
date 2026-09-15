#!/usr/bin/env python3
"""Read-only pinned clean detail CSV -> derived research JSON on stdout.

No database, writes, backtest reconstruction, runtime policy or broker dependency.
Missing source emits missing-evidence state; it never reconstructs trade rows.
"""
import argparse
import json
from pathlib import Path
from daxlab.detail_artifact_loader import preflight_detail_csv
from daxlab.reference.detail_artifacts import artifact_spec
from daxlab.research.failure_analysis import historical_risk_envelope


def analyze(path: Path | None):
    if path is None or not path.exists():
        return {'schema_version':'DAXLAB_HISTORICAL_RISK_ENVELOPE_V1', 'scope':'STATIC_DERIVED_RESEARCH_NOT_RUNTIME_RISK_OR_BROKER_FACT',
                'evidence_state':'INSUFFICIENT_SAMPLE', 'source_state':'WAITING_EXTERNAL_PINNED_TRADES_ARTIFACT',
                'observed_rows':0, 'mae_magnitude_r':None, 'mfe_r':None,
                'cost_stress':'UNKNOWN_NO_PER_TRADE_COST_EVIDENCE', 'survival_verdict':'UNVERIFIED_THRESHOLD',
                'execution_capability':'NONE', 'order_execution_enabled':False}
    preflight = preflight_detail_csv(content=path.read_bytes(), spec=artifact_spec('TRADES'))
    return historical_risk_envelope(preflight)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trades')
    args = parser.parse_args()
    print(json.dumps(analyze(Path(args.trades) if args.trades else None), sort_keys=True, allow_nan=False))
