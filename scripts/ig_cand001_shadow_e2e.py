"""One live IG read through existing CAND-001 SHADOW owners; no broker execution.

This is an isolated, one-shot host test, not a second strategy engine or daemon.
Complete checkpoint, decisions and operator telemetry share one atomic envelope.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ig_demo_readonly_probe import (  # noqa: E402
    DEFAULT_EPIC, DEFAULT_INSTRUMENT_ID, DEFAULT_MAX_AGE, TIMESTAMP_CONTRACT,
    _assert_credential_free, _fingerprint, collect_probe_with_candles,
)
from daxlab.runtime.atomic_json import atomic_write_json, read_json_object  # noqa: E402
from daxlab.adapters.ig_rest_readonly import IgReadOnlyError  # noqa: E402
from daxlab.runtime.candidate_config import Cand001Config  # noqa: E402
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy  # noqa: E402
from daxlab.runtime.candidate_operator_telemetry import (  # noqa: E402
    browser_operator_snapshot, validate_candidate_operator_snapshot,
)
from daxlab.runtime.candidate_shadow_checkpoint import (  # noqa: E402
    candidate_shadow_checkpoint_payload, parse_candidate_shadow_checkpoint_payload,
)
from daxlab.runtime.candidate_shadow_orchestrator import (  # noqa: E402
    Cand001ShadowState, process_cand001_shadow_candle,
)
from daxlab.runtime.contracts import Candle, RuntimeMode  # noqa: E402
from daxlab.runtime.decision import deterministic_decision_id, stable_fingerprint  # noqa: E402
from daxlab.runtime.manifests import RunManifest  # noqa: E402
from daxlab.runtime.operator_snapshot import parse_operator_snapshot_payload  # noqa: E402
from daxlab.runtime.paper_contracts import PaperFillModelConfig  # noqa: E402
from daxlab.runtime.single_instance import SingleInstanceLock  # noqa: E402

SCHEMA = "DAX_IG_CAND001_REAL_HOST_SHADOW_E2E_V2"
IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS = 60
STATE_DIR = Path(".runtime/ig_cand001_shadow_e2e_2233")
REPO = Path(__file__).resolve().parents[1]


class HostTestBlocked(RuntimeError):
    """Only fixed, credential-free codes cross the CLI boundary."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise HostTestBlocked(code)


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    require(result.tzinfo is not None and result.utcoffset() == timedelta(0), "CLOCK_INVALID_UTC")
    return result


def finalization_contract() -> dict[str, Any]:
    """Candidate eligibility policy, not a guarantee of provider immutability."""
    return {
        "contract": "IG_M5_CAND001_PROVIDER_FINALIZATION_GRACE_V1",
        "grace_seconds": IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS,
        "eligibility_clock": "PRICE_REQUEST_STARTED_AT_UTC",
    }


def finalized_rows(rows: list[dict[str, Any]], as_of: datetime) -> list[dict[str, Any]]:
    return [row for row in rows if (as_of - utc(row["close_time"])).total_seconds()
            >= IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS]


def manifest(head: str) -> RunManifest:
    return RunManifest.build(
        dataset_fingerprint=stable_fingerprint({
            "stream": "IG_READ_ONLY", "epic": DEFAULT_EPIC, "price": "MID_BID_ASK",
            "timestamp_contract": TIMESTAMP_CONTRACT, "symbol": "DE40", "timeframe": "5m",
            "provider_finalization": finalization_contract(),
        }),
        engine_fingerprint=stable_fingerprint({"exact_code_head": head, "owner": "CAND001_SHADOW",
                                               "fill_model": PaperFillModelConfig()}),
        config={"candidate": Cand001Config(), "sizing": Cand001SimulationSizingPolicy()},
        mode=RuntimeMode.SHADOW,
    )


def check_code(expected: str) -> str:
    require(re.fullmatch(r"[0-9a-f]{40}", expected) is not None, "GOVERNANCE_INVALID_HEAD")
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(REPO), *args], text=True, stderr=subprocess.DEVNULL,
        ).strip()
    head = git("rev-parse", "HEAD")
    require(head == expected, "GOVERNANCE_HEAD_MISMATCH")
    require(not git("status", "--porcelain", "--untracked-files=no"), "GOVERNANCE_TRACKED_DRIFT")
    require(not git("ls-files", "--others", "--exclude-standard", "scripts/*.py", "src/*.py"),
            "GOVERNANCE_UNTRACKED_CODE")
    for name, module in tuple(sys.modules.items()):
        source_file = getattr(module, "__file__", None)
        if name.startswith("daxlab.") and source_file:
            require(Path(source_file).resolve().is_relative_to(REPO / "src"),
                    "GOVERNANCE_IMPORT_PARITY")
    return head


def runtime_candles(rows: list[dict[str, Any]], observed: datetime) -> list[Candle]:
    """Explicit instrument/timeframe bridge; UTC, OHLC and source are preserved."""
    result = []
    for row in rows:
        require(row["source"] == f"IG_READ_ONLY:{DEFAULT_EPIC}:MID_BID_ASK", "ADAPTER_SOURCE_MISMATCH")
        start, close = utc(row["event_time"]), utc(row["close_time"])
        require(close - start == timedelta(minutes=5) and close <= observed,
                "ADAPTER_NOT_CLOSED_M5")
        require(close.second == close.microsecond == 0 and close.minute % 5 == 0,
                "ADAPTER_M5_ALIGNMENT")
        result.append(Candle(
            symbol="DE40", timeframe="5m", event_time=start, close_time=close,
            open=float(row["open"]), high=float(row["high"]), low=float(row["low"]),
            close=float(row["close"]), volume=row["volume"], source=row["source"],
            received_at=observed, is_closed=True,
        ))
    require(bool(result), "DATA_NO_CLOSED_M5")
    require(all(b.close_time - a.close_time == timedelta(minutes=5)
                for a, b in zip(result, result[1:])), "DATA_GAP_OR_ORDER")
    return result


def validate_evidence(payload: dict[str, Any], *, head: str, now: datetime,
                      current: bool = True) -> Cand001ShadowState:
    """Read back the persisted source evidence, never trust only its display DTO."""
    _assert_credential_free(payload)
    unhashed = dict(payload)
    digest = unhashed.pop("fingerprint", None)
    require(digest == _fingerprint(unhashed), "TELEMETRY_FINGERPRINT_MISMATCH")
    require(payload.get("schema") == SCHEMA
            and payload.get("provider_finalization_contract") == finalization_contract(),
            "STATE_FINALIZATION_CONTRACT_MIGRATION_REQUIRED")
    require(payload["exact_code_head"] == head, "STATE_CODE_OR_SCHEMA_DRIFT")
    require(payload["host_platform"] == "Windows" and payload["mode"] == "SHADOW",
            "GOVERNANCE_HOST_OR_MODE")
    require(payload["data_source"] == "IG_READ_ONLY" and payload["epic"] == DEFAULT_EPIC
            and payload["symbol"] == "DE40" and payload["candidate_id"] == "CAND-001",
            "GOVERNANCE_SOURCE_OR_CANDIDATE")
    require(payload["run_manifest"] == asdict(manifest(head)), "STATE_MANIFEST_DRIFT")
    require(payload["errors"] == [] and payload["protection_state"] == "UNKNOWN"
            and payload["reconciliation_state"] == "UNKNOWN", "GOVERNANCE_UNPROVEN_STATE")
    require(payload["execution_capability"] == "NONE" and payload["order_execution_enabled"] is False,
            "GOVERNANCE_EXECUTION_ENABLED")
    probe = payload["ig_probe"]
    raw_probe = dict(probe)
    require(raw_probe.pop("fingerprint") == _fingerprint(raw_probe), "DATA_PROBE_FINGERPRINT")
    require(probe["execution_capability"] == "NONE" and probe["order_execution_enabled"] is False,
            "GOVERNANCE_PROBE_EXECUTION")
    require(probe["m5_timestamp_contract"] == TIMESTAMP_CONTRACT
            and probe["m5_freshness_max_age_seconds"] == DEFAULT_MAX_AGE.total_seconds()
            and probe["m5_freshness_state"] == "FRESH", "DATA_CONTRACT_DRIFT")
    require(probe["market"]["epic"] == DEFAULT_EPIC, "DATA_EPIC_MISMATCH")
    nominal_rows = payload["ig_closed_m5_observation"]
    nominal_candles = runtime_candles(nominal_rows, utc(probe["observed_at_utc"]))
    require(nominal_rows[-1] == probe["latest_closed_m5"]
            and len(nominal_rows) == probe["closed_m5_count"],
            "DATA_PROJECTION_MISMATCH")
    require(probe["raw_m5_count"] == 40
            and probe["not_closed_m5_count"] == 40 - len(nominal_rows), "DATA_INCOMPLETE_RESPONSE")
    started = utc(probe["collection_started_at_utc"])
    requested = utc(probe["price_request_started_at_utc"])
    response = utc(probe["observed_at_utc"])
    processed = utc(payload["processed_at_utc"])
    exported = utc(payload["exported_at_utc"])
    require(started <= requested <= response <= processed <= exported <= now,
            "CLOCK_REVERSED")
    require(nominal_candles[-1].close_time <= requested, "DATA_NOT_CLOSED_AT_REQUEST")
    rows = finalized_rows(nominal_rows, requested)
    require(bool(rows), "STATE_NO_NEW_FINALIZED_M5")
    require(payload["input_window"] == rows and payload["latest_finalized_m5"] == rows[-1]
            and payload["candidate_finalized_m5_count"] == len(rows)
            and payload["not_finalized_m5_count"] == len(nominal_rows) - len(rows)
            and payload["finalization_as_of_utc"] == probe["price_request_started_at_utc"],
            "DATA_FINALIZATION_PROJECTION_MISMATCH")
    latest = utc(rows[-1]["close_time"])
    require(payload["candidate_m5_freshness_state"] == "FRESH"
            and payload["latest_finalized_m5_age_seconds"] == (processed - latest).total_seconds(),
            "DATA_FINALIZED_FRESHNESS_MISMATCH")
    require(IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS <= (exported - latest).total_seconds()
            <= DEFAULT_MAX_AGE.total_seconds(),
            "DATA_STALE_AT_EXPORT")
    if current:
        require(IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS <= (now - latest).total_seconds()
                <= DEFAULT_MAX_AGE.total_seconds(), "TELEMETRY_STALE")
    snapshot = payload["operator_snapshot"]
    parse_operator_snapshot_payload(snapshot)
    validate_candidate_operator_snapshot(snapshot)
    require(payload["operator_projection"] == browser_operator_snapshot(snapshot),
            "OPERATOR_PROJECTION_MISMATCH")
    require(snapshot["generated_at"] == payload["processed_at_utc"]
            and utc(snapshot["runtime"]["last_bar_close_time"]) == latest,
            "OPERATOR_OBSERVATION_MISMATCH")
    require(snapshot["runtime"]["health_state"] == "GREEN", "RUNTIME_NOT_GREEN")
    cfg = Cand001Config()
    require(snapshot["candidate_id"] == cfg.candidate_id
            and snapshot["config_fingerprint"] == stable_fingerprint(cfg), "OPERATOR_CONFIG_DRIFT")
    eligible_times = {row["close_time"] for row in rows}
    for index, item in enumerate(payload["decisions"]):
        record = item["record"]
        require(item["close_time"] in eligible_times
                and utc(record["event_time"]) == utc(item["close_time"]),
                "RUNTIME_UNFINALIZED_DECISION")
        require(item["scope"] == ("CURRENT" if index == len(payload["decisions"]) - 1 else "HISTORICAL_CATCHUP")
                and (index == 0 or utc(payload["decisions"][index - 1]["close_time"]) < utc(item["close_time"])),
                "RUNTIME_DECISION_ORDER_OR_SCOPE")
        require(record["decision_id"] == deterministic_decision_id(
            event_time=utc(record["event_time"]), data_fingerprint=record["data_fingerprint"],
            config_fingerprint=stable_fingerprint(cfg), core_version=cfg.product_identity().core_version,
        ), "RUNTIME_DECISION_ID_MISMATCH")
    require(snapshot["decision"]["decision_id"] == payload["decisions"][-1]["record"]["decision_id"],
            "OPERATOR_DECISION_MISMATCH")
    last = payload["decisions"][-1]
    require(last["scope"] == "CURRENT" and utc(last["close_time"]) == latest
            and last["record"]["final_action"] == snapshot["decision"]["action"]
            and last["admission_status"] == snapshot["admission"]["status"]
            and last["signal"]["direction"] == snapshot["signal"]["direction"]
            and last["signal"]["reason"] == snapshot["signal"]["reason"],
            "OPERATOR_PIPELINE_MISMATCH")
    require(payload["checkpoint"].get("run_manifest_fingerprint") == manifest(head).manifest_fingerprint,
            "STATE_MANIFEST_DRIFT")
    state = parse_candidate_shadow_checkpoint_payload(payload["checkpoint"], run_manifest=manifest(head))
    require(state.pipeline.signal.last_close_time == latest
            and state.pipeline.signal.session_date == payload["session_date"], "STATE_ANCHOR_MISMATCH")
    return state


def process_live_window(probe: dict[str, Any], rows: list[dict[str, Any]], *, head: str,
                        observed_at: datetime, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pure connection to existing owners. Only the CLI collects live host input."""
    received = utc(probe["observed_at_utc"])
    requested = utc(probe["price_request_started_at_utc"])
    require(requested <= received <= observed_at, "CLOCK_REVERSED")
    nominal_candles = runtime_candles(rows, received)
    require(nominal_candles[-1].close_time <= requested, "DATA_NOT_CLOSED_AT_REQUEST")
    eligible = finalized_rows(rows, requested)
    require(bool(eligible), "STATE_NO_NEW_FINALIZED_M5")
    candles = runtime_candles(eligible, received)
    require(IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS <= (observed_at - candles[-1].close_time).total_seconds()
            <= DEFAULT_MAX_AGE.total_seconds(),
            "DATA_STALE_AT_PROCESSING")
    run = manifest(head)
    state = Cand001ShadowState()
    pending = candles
    recovery = "FRESH_START"
    if prior is not None:
        state = validate_evidence(prior, head=head, now=observed_at, current=False)
        anchor = state.pipeline.signal.last_close_time
        prior_rows = {r["close_time"]: r for r in prior["input_window"]}
        for row in rows:
            if row["close_time"] in prior_rows:
                require(row == prior_rows[row["close_time"]], "STATE_CHANGED_OVERLAP")
        require(anchor in {c.close_time for c in candles}, "STATE_ANCHOR_NOT_FOUND")
        pending = [c for c in candles if c.close_time > anchor]
        require(bool(pending), "STATE_NO_NEW_FINALIZED_M5")
        recovery = "RESUME_ANCHOR_RECONCILED"
    decisions = []
    for candle in pending:
        result = process_cand001_shadow_candle(state, candle, observed_at=observed_at, run_manifest=run)
        state = result.state
        pipeline = result.pipeline_result
        decisions.append({
            "close_time": candle.close_time.isoformat(),
            "scope": "CURRENT" if candle is pending[-1] else "HISTORICAL_CATCHUP",
            "record": asdict(pipeline.decision),
            "signal": asdict(pipeline.signal), "admission_status": pipeline.admission.status.value,
            "trade_plan": asdict(pipeline.proposed_trade_plan) if pipeline.proposed_trade_plan else None,
        })
    snapshot = result.operator_snapshot.as_dict()
    payload = {
        "schema": SCHEMA, "exact_code_head": head, "host_platform": "Windows",
        "data_source": "IG_READ_ONLY", "epic": DEFAULT_EPIC, "symbol": "DE40", "mode": "SHADOW",
        "candidate_id": Cand001Config().candidate_id,
        "session_date": state.pipeline.signal.session_date,
        "run_manifest": asdict(run), "processed_at_utc": observed_at.isoformat(),
        "exported_at_utc": observed_at.isoformat(), "recovery_state": recovery,
        "provider_finalization_contract": finalization_contract(),
        "finalization_as_of_utc": probe["price_request_started_at_utc"],
        "candidate_finalized_m5_count": len(eligible), "not_finalized_m5_count": len(rows) - len(eligible),
        "latest_finalized_m5": eligible[-1], "candidate_m5_freshness_state": "FRESH",
        "latest_finalized_m5_age_seconds": (observed_at - candles[-1].close_time).total_seconds(),
        "execution_capability": "NONE", "order_execution_enabled": False,
        "protection_state": "UNKNOWN", "reconciliation_state": "UNKNOWN",
        "virtual_lifecycle_scope": "SHADOW_SIMULATION_ONLY_NOT_BROKER_EVIDENCE",
        "operator_scope": "LOCAL_VALIDATED_V3_DISPLAY_NOT_NEON_OR_MT5_CONSOLE",
        "ig_probe": probe, "ig_closed_m5_observation": rows, "input_window": eligible, "decisions": decisions,
        "checkpoint": candidate_shadow_checkpoint_payload(state, run_manifest=run),
        "operator_snapshot": snapshot, "operator_projection": browser_operator_snapshot(snapshot),
        "errors": [], "warnings": ["HISTORICAL_CATCHUP_IS_NOT_CURRENT_DECISION_EVIDENCE"],
    }
    if not state.pipeline.signal.or_complete:
        payload["warnings"].append("OPENING_RANGE_NOT_COMPLETE_NO_SIGNAL_IS_VALID")
    return json.loads(json.dumps(payload, default=lambda x: x.isoformat()))


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    snapshot = payload["operator_projection"]
    return {
        "status": "SHADOW_E2E_OBSERVED", "exact_code_head": payload["exact_code_head"],
        "observed_at_utc": payload["exported_at_utc"], "data_source": payload["data_source"],
        "candidate_id": payload["candidate_id"], "session_date": payload["session_date"],
        "recovery_state": payload["recovery_state"],
        "latest_closed_m5": snapshot["runtime"]["last_bar_close_time"],
        "latest_nominal_closed_m5": payload["ig_probe"]["latest_closed_m5"]["close_time"],
        "provider_finalization_contract": payload["provider_finalization_contract"],
        "candidate_finalized_m5_count": payload["candidate_finalized_m5_count"],
        "not_finalized_m5_count": payload["not_finalized_m5_count"],
        "m5_freshness_state": payload["candidate_m5_freshness_state"],
        "ig_probe_fingerprint": payload["ig_probe"]["fingerprint"],
        "operator_scope": payload["operator_scope"],
        "signal": snapshot["signal"], "admission": snapshot["admission"],
        "decision": snapshot["decision"], "runtime": snapshot["runtime"],
        "virtual_position": snapshot["virtual_position"], "warnings": payload["warnings"],
        "execution_capability": "NONE", "order_execution_enabled": False,
        "fingerprint": payload["fingerprint"],
    }


def require_verified_live_provider_contract() -> None:
    """Quarantine the disproven60s live policy until RAW semantics is established.

    No CLI override. Historical offline regressions and hash-bound local reads
    remain available; this is not a replacement timestamp/finalization rule.
    """
    raise HostTestBlocked("DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--credentials-file", type=Path)
    source.add_argument("--read-evidence", type=Path)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-fingerprint")
    parser.add_argument("--state-dir", type=Path, default=STATE_DIR)
    args = parser.parse_args()
    stage = "GOVERNANCE"
    try:
        head = check_code(args.expected_head)
        if args.read_evidence:
            stage = "OPERATOR"
            payload = read_json_object(args.read_evidence)
            require(args.expected_fingerprint == payload.get("fingerprint"),
                    "OPERATOR_EXPECTED_FINGERPRINT_REQUIRED_OR_MISMATCH")
            validate_evidence(payload, head=head, now=datetime.now(timezone.utc))
        else:
            require(platform.system() == "Windows", "GOVERNANCE_WINDOWS_HOST_REQUIRED")
            stage = "STATE"
            evidence_file = args.state_dir / "evidence.json"
            with SingleInstanceLock(args.state_dir / "writer.lock", "IG_CAND001_SHADOW_E2E"):
                prior = read_json_object(evidence_file) if evidence_file.exists() else None
                if prior is not None:
                    validate_evidence(prior, head=head, now=datetime.now(timezone.utc), current=False)
                stage = "DATA"
                require_verified_live_provider_contract()
                probe, rows = collect_probe_with_candles(
                    credentials_file=args.credentials_file, epic=DEFAULT_EPIC,
                    instrument_id=DEFAULT_INSTRUMENT_ID, bars=40,
                )
                stage = "RUNTIME"
                payload = process_live_window(probe, rows, head=head,
                                              observed_at=datetime.now(timezone.utc), prior=prior)
                payload["exported_at_utc"] = datetime.now(timezone.utc).isoformat()
                payload["fingerprint"] = _fingerprint(payload)
                validate_evidence(payload, head=head, now=datetime.now(timezone.utc))
                check_code(head)
                stage = "TELEMETRY"
                atomic_write_json(evidence_file, payload)
                payload = read_json_object(evidence_file)
                validate_evidence(payload, head=head, now=datetime.now(timezone.utc))
        print(json.dumps(summary(payload), indent=2))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, HostTestBlocked) else f"{stage}_TEST_FAILED"
        if stage == "DATA" and isinstance(exc, IgReadOnlyError) and re.search(r"\bHTTP 401\b", str(exc)):
            code = "IG_AUTHENTICATION_FAILED_NO_RETRY"
        print(json.dumps({"status": "BLOCKED", "error_code": code,
                          "prior_evidence_is_not_current": True,
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
