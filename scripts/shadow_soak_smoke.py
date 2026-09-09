"""Run a deterministic 30-session synthetic SHADOW soak with no order capability."""
from __future__ import annotations

from daxlab.runtime.shadow_soak import run_shadow_soak, soak_summary
from daxlab.runtime.shadow_soak_fixture import SESSIONS, build_bars


def main() -> None:
    bars = build_bars()
    first = run_shadow_soak(bars)
    second = run_shadow_soak(bars)
    if first != second:
        raise SystemExit("SHADOW soak smoke failed: deterministic rerun drift")
    if any(item.action != "NO_ORDER" for item in first.decisions):
        raise SystemExit("SHADOW soak smoke failed: order-capable output")
    summary = soak_summary(first)
    print(
        "SHADOW soak smoke OK | "
        f"surface={summary['evidence_state']} | sessions={SESSIONS} | bars={len(bars)} | "
        f"blocked={summary['blocked']} | execution={summary['execution_capability']} | "
        f"fingerprint={summary['run_fingerprint']}"
    )
    print("Real MT5 broker evidence: NOT PRESENT | Paper: NOT STARTED | Live: NOT AUTHORIZED")


if __name__ == "__main__":
    main()
