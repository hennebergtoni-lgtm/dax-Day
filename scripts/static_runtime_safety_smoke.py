"""Deterministic static/runtime-boundary safety smoke with no broker order path.

Web V2 deliberately excludes current host/runtime truth. This smoke checks only
durable static safety truth plus duplicate-safe synthetic SHADOW recovery; real
host readiness is owned by the separate runtime evidence path.
"""
from __future__ import annotations

import json
from pathlib import Path

from daxlab.runtime.shadow_soak import SoakFault, run_shadow_soak
from daxlab.runtime.shadow_soak_fixture import build_bars


_FORBIDDEN_DYNAMIC_WEB_SECTIONS = {
    "mt5_adapter",
    "host_readiness",
    "pre_host_gate",
    "synthetic_shadow_soak",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    bars = build_bars()[:2]

    first = run_shadow_soak(bars[:1], faults={0: SoakFault(feed_fresh=False)})
    resumed = run_shadow_soak(bars[:1], checkpoint=first.checkpoint)

    if first.checkpoint.schema_version != "DAXLAB_SHADOW_SOAK_CHECKPOINT_V2":
        raise SystemExit("SHADOW checkpoint V2 missing")
    if resumed.duplicates_suppressed != 1 or resumed.decisions != ():
        raise SystemExit("same closed bar was not suppressed across changed safety state")

    if web.get("schema_version") != "DAXLAB_WEB_STATIC_STATUS_V2":
        raise SystemExit("static web status must use V2 schema")
    if web.get("runtime_truth_included") is not False:
        raise SystemExit("static web status must not claim current runtime truth")
    leaked = sorted(_FORBIDDEN_DYNAMIC_WEB_SECTIONS.intersection(web))
    if leaked:
        raise SystemExit(f"dynamic runtime sections leaked into static web status: {leaked}")

    boundary = web.get("runtime_boundary")
    if not isinstance(boundary, dict):
        raise SystemExit("static web status must expose runtime boundary")
    if boundary.get("browser_runtime_endpoint") != "NOT_IMPLEMENTED":
        raise SystemExit("static web must not fabricate browser runtime endpoint")

    paper = web.get("paper_preparation")
    readiness = web.get("readiness")
    if not isinstance(paper, dict) or not isinstance(readiness, dict):
        raise SystemExit("static web safety sections missing")
    if paper.get("paper_started") is not False or paper.get("broker_adapter_present") is not False:
        raise SystemExit("Paper must remain not started and broker adapter absent")
    if readiness.get("paper") != "BLOCKED" or readiness.get("live") != "BLOCKED":
        raise SystemExit("Paper and LIVE must remain blocked")

    print(
        "Static runtime safety smoke OK | checkpoint V2 | duplicate-safe | "
        "runtime truth external | Paper/Live BLOCKED | NO_ORDER"
    )


if __name__ == "__main__":
    main()
