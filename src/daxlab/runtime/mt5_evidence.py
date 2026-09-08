"""Immutable, credential-free evidence for synthetic/read-only MT5 host observations."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

_FORBIDDEN = {"password","passwd","login","account","account_id","account_number","otp","token","secret","api_key"}

@dataclass(frozen=True, slots=True)
class Mt5HostEvidence:
    schema_version: str
    evidence_id: str
    payload_sha256: str
    observed_at: str
    kind: str
    payload: Mapping[str, Any]


def canonical_payload(payload: Mapping[str, Any]) -> str:
    _assert_safe(payload)
    return json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=True)


def build_host_evidence(*, observed_at: datetime, kind: str, payload: Mapping[str, Any]) -> Mt5HostEvidence:
    if observed_at.tzinfo is None: raise ValueError("observed_at must be timezone-aware")
    if not kind or not isinstance(kind,str): raise ValueError("kind must be non-empty")
    canonical=canonical_payload(payload)
    digest=sha256(canonical.encode()).hexdigest()
    identity_source=f"MT5_HOST_EVIDENCE_V1|{kind}|{observed_at.isoformat()}|{digest}"
    evidence_id=sha256(identity_source.encode()).hexdigest()
    return Mt5HostEvidence("MT5_HOST_EVIDENCE_V1",evidence_id,digest,observed_at.isoformat(),kind,dict(payload))


def recovery_manifest_entry(evidence: Mt5HostEvidence) -> dict[str,str]:
    return {"type":"MT5_HOST_EVIDENCE","schema_version":evidence.schema_version,
            "evidence_id":evidence.evidence_id,"payload_sha256":evidence.payload_sha256}


def write_host_evidence(path: Path, evidence: Mt5HostEvidence) -> None:
    text=json.dumps(asdict(evidence),sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n"
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")


def read_host_evidence(path: Path) -> Mt5HostEvidence:
    raw=json.loads(path.read_text(encoding="utf-8")); expected={"schema_version","evidence_id","payload_sha256","observed_at","kind","payload"}
    if set(raw)!=expected: raise ValueError("invalid MT5 evidence fields")
    observed=datetime.fromisoformat(raw["observed_at"])
    rebuilt=build_host_evidence(observed_at=observed,kind=raw["kind"],payload=raw["payload"])
    if rebuilt.schema_version!=raw["schema_version"] or rebuilt.evidence_id!=raw["evidence_id"] or rebuilt.payload_sha256!=raw["payload_sha256"]:
        raise ValueError("MT5 evidence hash/identity conflict")
    return rebuilt


def detect_evidence_conflict(existing: Mt5HostEvidence, incoming: Mt5HostEvidence) -> str:
    if existing.evidence_id==incoming.evidence_id and existing.payload_sha256==incoming.payload_sha256: return "DUPLICATE_IDENTICAL"
    if existing.evidence_id==incoming.evidence_id: return "CONFLICT_SAME_ID_DIFFERENT_PAYLOAD"
    return "DISTINCT"


def _assert_safe(value: Any, path: str="payload") -> None:
    if isinstance(value,Mapping):
        for key,item in value.items():
            key_text=str(key); lowered=key_text.lower()
            if lowered in _FORBIDDEN or any(term in lowered for term in ("password","secret","otp","account_number","api_key")):
                raise ValueError(f"forbidden credential/account field at {path}.{key_text}")
            _assert_safe(item,f"{path}.{key_text}")
    elif isinstance(value,(list,tuple)):
        for i,item in enumerate(value): _assert_safe(item,f"{path}[{i}]")
