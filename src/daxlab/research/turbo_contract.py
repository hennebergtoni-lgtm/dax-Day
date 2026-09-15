"""Development-only Turbo contracts. Integrity is not source authenticity.

No credentials, broker ports, runtime mutation, promotion or deployment authority.
Reuses V1 subject/hash/time semantics without changing its closed runtime schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
import re

from daxlab.runtime.bot_helper_contract import HelperSubject, digest, read_utc, require_sha

SCOPES = frozenset({'SYNTHETIC', 'REPLAY', 'CI', 'LOCAL_TEST', 'REAL_HOST',
                    'REAL_BROKER_READ', 'REAL_BROKER_EXECUTION'})
RIGHTS = frozenset({'READ', 'WRITE', 'SUGGEST', 'CREATE_HYPOTHESIS', 'CREATE_CHALLENGER',
                   'RUN_SYNTHETIC_TEST', 'RUN_REPLAY', 'RUN_RESEARCH', 'RUN_OOS_WF',
                   'RUN_SHADOW', 'PUBLISH_EVIDENCE', 'VETO_PROMOTION', 'PROMOTE', 'DEPLOY',
                   'MUTATE_RUNTIME', 'CHANGE_RISK', 'CHANGE_FILTERS', 'EXECUTE_ORDER'})
COMMON = frozenset({'READ', 'WRITE', 'SUGGEST', 'RUN_SYNTHETIC_TEST', 'RUN_REPLAY',
                   'PUBLISH_EVIDENCE'})
ROLE_RIGHTS = {'L': COMMON | {'CREATE_HYPOTHESIS', 'RUN_RESEARCH'},
               'E': COMMON | {'CREATE_HYPOTHESIS', 'CREATE_CHALLENGER', 'RUN_RESEARCH',
                              'RUN_OOS_WF', 'RUN_SHADOW'},
               'G': COMMON | {'RUN_RESEARCH', 'RUN_OOS_WF', 'RUN_SHADOW', 'VETO_PROMOTION'}}


def authorize(role: str, right: str) -> None:
    if role not in ROLE_RIGHTS or right not in RIGHTS or right not in ROLE_RIGHTS[role]:
        raise PermissionError('TURBO_AUTHORITY_DENIED')


def token(value: str) -> None:
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_.:/-]{1,180}', value) is None:
        raise ValueError('TURBO_INVALID_TOKEN')
    if any(word in value.lower() for word in ('password', 'bearer', 'postgres:', 'secret=')):
        raise ValueError('TURBO_UNSAFE_TOKEN')
    if value.upper() in {'GUARANTEED', 'CERTAIN', 'SAFE_WIN', 'SURE_WIN', 'CANT_LOSE', 'CAN_ONLY_GO_WELL'}:
        raise ValueError('TURBO_CERTAINTY_CLAIM_FORBIDDEN')


def finite(value: float, minimum: float | None = None) -> None:
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError('TURBO_NONFINITE_NUMBER')
    if minimum is not None and value < minimum:
        raise ValueError('TURBO_NUMBER_BOUND')


def count(value: int, minimum=0, maximum=1_000_000) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('TURBO_COUNT_BOUND')


def tokens(values: tuple[str, ...], *, required=False) -> None:
    if type(values) is not tuple or len(values) > 256 or len(values) != len(set(values)):
        raise ValueError('TURBO_INVALID_COLLECTION')
    if required and not values:
        raise ValueError('TURBO_MISSING_EVIDENCE')
    for value in values:
        token(value)


@dataclass(frozen=True, slots=True)
class Provenance:
    evidence_head: str
    continuity_anchor: str
    runtime_build: str
    config_fingerprint: str
    data_contract: str
    evidence_scope: str
    observed_at: str
    generated_at: str
    valid_until: str | None
    subject: HelperSubject
    evidence_refs: tuple[str, ...]
    superseded_by: str | None = None

    def __post_init__(self):
        require_sha(self.evidence_head, 40)
        require_sha(self.continuity_anchor, 40)
        for value in (self.runtime_build, self.config_fingerprint, self.data_contract):
            require_sha(value)
        if type(self.subject) is not HelperSubject:
            raise ValueError('TURBO_SUBJECT_REQUIRED')
        self.subject.__post_init__()
        if self.subject.code_head != self.evidence_head:
            raise ValueError('TURBO_SUBJECT_HEAD_MISMATCH')
        if self.subject.config_fingerprint != self.config_fingerprint:
            raise ValueError('TURBO_SUBJECT_CONFIG_MISMATCH')
        if self.evidence_scope not in SCOPES:
            raise ValueError('TURBO_SCOPE_INVALID')
        if self.evidence_scope.startswith('REAL_') and self.subject.provider in {'SYNTHETIC', 'REPLAY'}:
            raise ValueError('TURBO_SCOPE_CONTRADICTION')
        if read_utc(self.observed_at) > read_utc(self.generated_at):
            raise ValueError('TURBO_FUTURE_OBSERVATION')
        if self.valid_until is not None and read_utc(self.valid_until) < read_utc(self.observed_at):
            raise ValueError('TURBO_VALIDITY_INVALID')
        tokens(self.evidence_refs, required=True)
        for ref in self.evidence_refs:
            require_sha(ref)
        if self.superseded_by is not None:
            require_sha(self.superseded_by)

    @property
    def fingerprint(self):
        return digest(asdict(self))

    @classmethod
    def from_payload(cls, payload: dict):
        from daxlab.domain.market import InstrumentId
        safe_tree(payload)
        values = dict(payload)
        subject = dict(values['subject'])
        subject['instrument_id'] = InstrumentId(**subject['instrument_id'])
        values['subject'] = HelperSubject(**subject)
        values['evidence_refs'] = tuple(values['evidence_refs'])
        result = cls(**values)
        if digest(asdict(result)) != digest(payload):
            raise ValueError('TURBO_PROVENANCE_SCHEMA')
        return result

    def matches(self, expected: Provenance, *, now: str, scopes: tuple[str, ...]) -> bool:
        self.__post_init__()
        expected.__post_init__()
        instant = read_utc(now)
        return (self.superseded_by is None and self.evidence_scope in scopes
                and self.valid_until is not None
                and read_utc(self.observed_at) <= instant <= read_utc(self.valid_until)
                and read_utc(self.generated_at) <= instant
                and all(getattr(self, field) == getattr(expected, field) for field in (
                    'evidence_head', 'runtime_build', 'config_fingerprint',
                    'data_contract', 'subject')))


def research_payload(kind: str, **fields) -> dict:
    token(kind)
    if set(fields) & {'schema', 'kind', 'execution_capability', 'order_execution_enabled', 'runtime_actuation'}:
        raise ValueError('TURBO_RESERVED_OUTPUT_FIELD')
    value = {'schema': 'DAX_TURBO_V1_1', 'kind': kind, **fields,
             'execution_capability': 'NONE', 'order_execution_enabled': False,
             'runtime_actuation': False}
    digest(value)  # strict JSON / finite-number check
    return value


@dataclass(frozen=True, slots=True)
class HistoricalClaim:
    """Documented real observation with incomplete original runtime provenance.

    The claim is preserved as historical VERIFIED; it can never act as a fresh
    Provenance receipt. Unknown original time/account/build are not reconstructed.
    """
    dimension_id: str
    evidence_head: str
    continuity_anchor: str
    evidence_scope: str
    source_ref: str
    observed_date: str
    attribution: str = 'OPERATOR_REPORTED_REPOSITORY_CLOSEOUT'

    def __post_init__(self):
        from datetime import date
        token(self.dimension_id)
        require_sha(self.evidence_head, 40)
        require_sha(self.continuity_anchor, 40)
        require_sha(self.source_ref)
        if self.evidence_scope not in SCOPES or date.fromisoformat(self.observed_date).isoformat() != self.observed_date:
            raise ValueError('HISTORICAL_CLAIM_SCOPE_DATE')
        if self.attribution != 'OPERATOR_REPORTED_REPOSITORY_CLOSEOUT':
            raise ValueError('HISTORICAL_CLAIM_ATTRIBUTION')


def safe_tree(value, *, depth=0) -> None:
    """Bounded development artifact sanitation, including values, not only keys."""
    if depth > 12:
        raise ValueError('TURBO_PAYLOAD_DEPTH')
    if isinstance(value, dict):
        if len(value) > 256:
            raise ValueError('TURBO_PAYLOAD_WIDTH')
        for k, v in value.items():
            token(k)
            safe_tree(v, depth=depth+1)
    elif isinstance(value, (list, tuple)):
        if len(value) > 10000:
            raise ValueError('TURBO_PAYLOAD_LENGTH')
        for v in value:
            safe_tree(v, depth=depth+1)
    elif isinstance(value, str):
        if len(value) > 4096 or re.search(
                r'(?i)(bearer\s|postgres(?:ql)?://|-----BEGIN|api[_-]?key\s*[:=]|'
                r'password\s*[:=]|token\s*[:=]|secret\s*[:=])', value):
            raise ValueError('TURBO_UNSAFE_VALUE')
    elif type(value) in (float, int):
        finite(value)
    elif value is not None and type(value) is not bool:
        raise ValueError('TURBO_PAYLOAD_TYPE')
