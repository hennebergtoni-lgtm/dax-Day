"""Research registry: experiments are explicit records, never implicit notebook state."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from daxlab.contracts import ExperimentManifest


class ExperimentRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, experiment_id: str) -> Path:
        return self.root / experiment_id / "manifest.json"

    def save(self, manifest: ExperimentManifest) -> Path:
        path = self.path_for(manifest.experiment_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(manifest)
        payload["status"] = manifest.status.value
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path


class TurboLedger:
    """Specialized append-only development journal on the existing registry backbone.

    Single writer, immutable numbered receipts, existing atomic JSON publisher.
    A held lock after interruption fails closed; no silent stale-lock stealing.
    External checkpoint pin detects suffix truncation; a hash alone cannot.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def read(self, *, expected_head: str | None = None) -> tuple[dict, ...]:
        from daxlab.runtime.atomic_json import read_json_object
        from daxlab.runtime.bot_helper_contract import digest
        rows = []
        previous = '0' * 64
        for number, path in enumerate(sorted(self.root.glob('*.json'))):
            if path.name != f'{number:08d}.json':
                raise ValueError('TURBO_LEDGER_SEQUENCE')
            row = read_json_object(path)
            if set(row) != {'sequence', 'previous_hash', 'kind', 'record_id', 'body', 'hash'}:
                raise ValueError('TURBO_LEDGER_SCHEMA')
            core = {k: v for k, v in row.items() if k != 'hash'}
            if row['sequence'] != number or row['previous_hash'] != previous or digest(core) != row['hash']:
                raise ValueError('TURBO_LEDGER_TAMPER')
            self._validate_body(row['kind'], row['record_id'], row['body'])
            if any(r['record_id'] == row['record_id'] for r in rows):
                raise ValueError('TURBO_LEDGER_DUPLICATE')
            previous = row['hash']
            rows.append(row)
        if expected_head is not None and previous != expected_head:
            raise ValueError('TURBO_LEDGER_CHECKPOINT_MISMATCH')
        return tuple(rows)

    @staticmethod
    def _validate_body(kind, record_id, body):
        from daxlab.research.turbo_contract import safe_tree, token
        from daxlab.research.turbo_learning import Lesson
        from daxlab.research.turbo_experiment import Hypothesis
        token(record_id)
        if type(body) is not dict or kind not in {'LESSON', 'HYPOTHESIS', 'TRIAL', 'RESULT', 'JUDGMENT', 'DONOR'}:
            raise ValueError('TURBO_LEDGER_BODY_SCHEMA')
        safe_tree(body)
        try:
            if kind == 'LESSON' and Lesson.from_payload(body).incident.incident_id != record_id:
                raise ValueError('LESSON_ID_BINDING')
            if kind == 'HYPOTHESIS' and Hypothesis.from_payload(body).hypothesis_id != record_id:
                raise ValueError('HYPOTHESIS_ID_BINDING')
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError('TURBO_LEDGER_BODY_SCHEMA') from exc

    def append(self, *, role: str, kind: str, record_id: str, body: dict,
               expected_head: str) -> str:
        from daxlab.research.turbo_contract import authorize, token, safe_tree
        from daxlab.runtime.atomic_json import atomic_write_json
        from daxlab.runtime.bot_helper_contract import digest, require_sha
        from daxlab.runtime.mt5_evidence import _assert_safe
        authorize(role, 'WRITE')
        owner = {'LESSON': 'L', 'HYPOTHESIS': 'E', 'TRIAL': 'E', 'RESULT': 'E',
                 'JUDGMENT': 'G', 'DONOR': 'E'}
        if owner.get(kind) != role:
            raise PermissionError('TURBO_LEDGER_OWNER')
        token(record_id)
        require_sha(expected_head)
        _assert_safe(body)
        safe_tree(body)
        self._validate_body(kind, record_id, body)
        encoded = json.dumps(body, sort_keys=True, allow_nan=False)
        if len(encoded) > 512_000:
            raise ValueError('TURBO_LEDGER_BOUND')
        self.root.mkdir(parents=True, exist_ok=True)
        lock = self.root / 'writer.lock'
        # Existence is the lock. Close the handle before cleanup for Windows.
        with lock.open('x'):
            pass
        try:
            rows = self.read(expected_head=expected_head)
            if any(r['record_id'] == record_id for r in rows):
                raise ValueError('TURBO_LEDGER_DUPLICATE')
            if kind == 'HYPOTHESIS' and body.get('exploratory') is False:
                from daxlab.research.turbo_contract import read_utc
                holds = body['holdout_ids']
                consumed = {h for r in rows if r['kind'] == 'HYPOTHESIS'
                            and r['body'].get('exploratory') is False
                            for h in r['body']['holdout_ids']}
                if consumed.intersection(holds):
                    raise ValueError('PERSISTED_HOLDOUT_ALREADY_CONSUMED')
                # Renaming/re-hashing a dataset must not launder the same OOS
                # period back into confirmatory research on this instrument.
                for row in rows:
                    prior = row['body']
                    if row['kind'] != 'HYPOTHESIS':
                        continue
                    if prior['provenance']['subject']['instrument_id'] != body['provenance']['subject']['instrument_id']:
                        continue
                    for _, start, end in body['holdout_windows']:
                        if any(max(read_utc(start), read_utc(a)) < min(read_utc(end), read_utc(b))
                               for _, a, b in prior.get('holdout_windows', [])):
                            raise ValueError('PERSISTED_HOLDOUT_PERIOD_ALREADY_CONSUMED')
            core = dict(sequence=len(rows), previous_hash=expected_head, kind=kind,
                        record_id=record_id, body=json.loads(encoded))
            result = digest(core)
            atomic_write_json(self.root / f'{len(rows):08d}.json',
                              core | {'hash': result}, overwrite=False)
            return result
        finally:
            lock.unlink()

    def prior_lessons(self, *, failure_class: str, affected_owners: tuple,
                      contract_fingerprint: str) -> tuple[dict, ...]:
        return tuple(row for row in self.read() if row['kind'] == 'LESSON'
                     and row['body'].get('failure_class') == failure_class
                     and set(row['body'].get('affected_owners', ())) == set(affected_owners)
                     and row['body'].get('contract_fingerprint') == contract_fingerprint)

    def append_lesson(self, lesson, *, expected_head: str) -> str:
        from daxlab.research.turbo_learning import Lesson
        if type(lesson) is not Lesson:
            raise ValueError('TYPED_LESSON_REQUIRED')
        return self.append(role='L', kind='LESSON', record_id=lesson.incident.incident_id,
                           body=lesson.to_payload(), expected_head=expected_head)

    def declare_hypothesis(self, hypothesis, *, expected_head: str) -> str:
        from daxlab.research.turbo_experiment import Hypothesis
        if type(hypothesis) is not Hypothesis:
            raise ValueError('TYPED_HYPOTHESIS_REQUIRED')
        hypothesis.__post_init__()
        body = json.loads(json.dumps(asdict(hypothesis)))
        return self.append(role='E', kind='HYPOTHESIS', record_id=hypothesis.hypothesis_id,
                           body=body, expected_head=expected_head)

    def publish_evaluation(self, challenger, bundle, *, outcomes: tuple, expected_head: str) -> str:
        """E publishes a sealed research bundle against its actual trial journal."""
        from daxlab.research.turbo_contract import digest
        from daxlab.research.turbo_experiment import check_trial_accounting
        from daxlab.research.variant_trial_registry import TrialDeclaration
        bundle.__post_init__()
        rows = self.read(expected_head=expected_head)
        h = challenger.hypothesis
        declared = [r for r in rows if r['kind'] == 'HYPOTHESIS' and r['record_id'] == h.hypothesis_id]
        if len(declared) != 1 or digest(declared[0]['body']) != h.fingerprint:
            raise ValueError('EVALUATION_HYPOTHESIS_NOT_JOURNALLED')
        declarations = tuple(TrialDeclaration(**r['body']) for r in rows if r['kind'] == 'TRIAL'
                             and r['body'].get('hypothesis_trial_id') == h.hypothesis_id)
        accounting = check_trial_accounting(h, declarations, outcomes, budget=len(h.trial_ids))
        if bundle.accounting_ref != accounting or bundle.challenger_fingerprint != digest(asdict(challenger)):
            raise ValueError('EVALUATION_ACCOUNTING_MISMATCH')
        return self.append(role='E', kind='RESULT', record_id=h.hypothesis_id+'.evaluation',
            body={'bundle': asdict(bundle), 'outcomes': outcomes, 'accounting_ref': accounting},
            expected_head=expected_head)
