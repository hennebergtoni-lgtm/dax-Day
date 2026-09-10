from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "DAXLAB_VARIANT_TRIAL_REGISTRY_V1"
GENESIS_HASH = "0" * 64
PREDECLARED = "PREDECLARED"
RETROACTIVE = "RETROACTIVE_RECONSTRUCTED"
_ALLOWED_MODES = {PREDECLARED, RETROACTIVE}


@dataclass(frozen=True)
class TrialDeclaration:
    trial_id: str
    experiment_id: str
    hypothesis_trial_id: str
    family_id: str
    variant_key: str
    parameters: Mapping[str, Any]
    declared_at_utc: str
    declaration_mode: str
    source_commit: str
    previous_hash: str
    record_hash: str

    @property
    def independently_predeclared(self) -> bool:
        return self.declaration_mode == PREDECLARED

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["parameters"] = dict(self.parameters)
        payload["independently_predeclared"] = self.independently_predeclared
        return payload


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize_timestamp(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("declared_at_utc must be non-empty")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("declared_at_utc must be an explicit UTC timestamp")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_nonempty(value: str, label: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _hash_record(core: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(core).encode("utf-8")).hexdigest()


def declare_trial(
    existing: Iterable[TrialDeclaration],
    *,
    trial_id: str,
    experiment_id: str,
    hypothesis_trial_id: str,
    family_id: str,
    variant_key: str,
    parameters: Mapping[str, Any],
    declared_at_utc: str,
    declaration_mode: str,
    source_commit: str,
) -> TrialDeclaration:
    """Create one immutable declaration linked to the previous declaration hash."""
    rows = list(existing)
    verify_trial_chain(rows)

    normalized_trial_id = _validate_nonempty(trial_id, "trial_id")
    if normalized_trial_id in {row.trial_id for row in rows}:
        raise ValueError("trial_id must be unique")

    mode = declaration_mode.strip().upper()
    if mode not in _ALLOWED_MODES:
        raise ValueError("unsupported declaration_mode")
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be a mapping")
    try:
        _canonical_json(dict(parameters))
    except (TypeError, ValueError) as exc:
        raise ValueError("parameters must be JSON-serializable") from exc

    previous_hash = rows[-1].record_hash if rows else GENESIS_HASH
    core = {
        "trial_id": normalized_trial_id,
        "experiment_id": _validate_nonempty(experiment_id, "experiment_id"),
        "hypothesis_trial_id": _validate_nonempty(
            hypothesis_trial_id, "hypothesis_trial_id"
        ),
        "family_id": _validate_nonempty(family_id, "family_id"),
        "variant_key": _validate_nonempty(variant_key, "variant_key"),
        "parameters": dict(parameters),
        "declared_at_utc": _normalize_timestamp(declared_at_utc),
        "declaration_mode": mode,
        "source_commit": _validate_nonempty(source_commit, "source_commit"),
        "previous_hash": previous_hash,
    }
    return TrialDeclaration(**core, record_hash=_hash_record(core))


def verify_trial_chain(rows: Iterable[TrialDeclaration]) -> str:
    """Fail closed on duplicate IDs, broken links, or modified declaration content."""
    expected_previous = GENESIS_HASH
    seen: set[str] = set()
    last_hash = GENESIS_HASH
    for row in rows:
        if row.trial_id in seen:
            raise ValueError("duplicate trial_id in registry")
        seen.add(row.trial_id)
        if row.declaration_mode not in _ALLOWED_MODES:
            raise ValueError("unsupported declaration_mode in registry")
        if row.previous_hash != expected_previous:
            raise ValueError("broken previous_hash link")
        core = {
            "trial_id": row.trial_id,
            "experiment_id": row.experiment_id,
            "hypothesis_trial_id": row.hypothesis_trial_id,
            "family_id": row.family_id,
            "variant_key": row.variant_key,
            "parameters": dict(row.parameters),
            "declared_at_utc": _normalize_timestamp(row.declared_at_utc),
            "declaration_mode": row.declaration_mode,
            "source_commit": row.source_commit,
            "previous_hash": row.previous_hash,
        }
        expected_hash = _hash_record(core)
        if row.record_hash != expected_hash:
            raise ValueError("record_hash mismatch")
        expected_previous = row.record_hash
        last_hash = row.record_hash
    return last_hash


def registry_payload(rows: Iterable[TrialDeclaration]) -> dict[str, Any]:
    declarations = list(rows)
    head_hash = verify_trial_chain(declarations)
    return {
        "schema_version": SCHEMA_VERSION,
        "append_only": True,
        "hash_chain": "SHA256_PREVIOUS_HASH",
        "head_hash": head_hash,
        "trial_count": len(declarations),
        "predeclared_trial_ids": [
            row.trial_id for row in declarations if row.independently_predeclared
        ],
        "declarations": [row.to_payload() for row in declarations],
    }
