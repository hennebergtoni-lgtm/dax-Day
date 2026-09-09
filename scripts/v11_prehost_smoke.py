"""Deterministic pre-host V11 safety smoke. No broker connection or order path."""
from __future__ import annotations

import json
from pathlib import Path

from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak
from daxlab.runtime.shadow_soak_fixture import build_bars


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    bars = build_bars()[:2]

    first = run_shadow_soak(bars[:1], faults={0: SoakFault(feed_fresh=False)})
    resumed = run_shadow_soak(bars[:1], checkpoint=first.checkpoint)

    if first.checkpoint.schema_version != "DAXLAB_SHADOW_SOAK_CHECKPOINT_V2":
        raise SystemExit("V11 checkpoint V2 missing")
    if resumed.duplicates_suppressed != 1 or resumed.decisions != ():
        raise SystemExit("same closed bar was not suppressed across changed safety state")
    if web["pre_host_gate"]["external_mt5_milestones_102_110_complete"] is not False:
        raise SystemExit("external MT5 milestones must remain incomplete")
    if web["pre_host_gate"]["next_external_milestone"] != 102:
        raise SystemExit("next external milestone must be 102")
    if web["pre_host_gate"]["paper_started"] is not False:
        raise SystemExit("Paper must remain not started")
    if web["pre_host_gate"]["live_authorized"] is not False:
        raise SystemExit("LIVE must remain unauthorized")
    if web["pre_host_gate"]["order_execution_enabled"] is not False:
        raise SystemExit("order execution must remain disabled")

    print("V11 pre-host smoke OK | checkpoint V2 | duplicate-safe | next external milestone 102 | NO_ORDER")


if __name__ == "__main__":
    main()
