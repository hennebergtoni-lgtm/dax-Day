"""G: independent sealed-evidence judgment. No promotion or proposal API."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from daxlab.research.turbo_contract import (
    Provenance, authorize, digest, require_sha, research_payload, token,
)
from daxlab.research.turbo_experiment import CHECKS, Challenger


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: str
    evidence_ref: str
    rationale: str

    def __post_init__(self):
        if self.name not in CHECKS or self.status not in {'PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE'}:
            raise ValueError('JUDGE_CHECK_SCHEMA')
        require_sha(self.evidence_ref)
        token(self.rationale)
        if self.status == 'NOT_APPLICABLE' and self.name not in {'PBO', 'DSR', 'SPA'}:
            raise ValueError('JUDGE_REQUIRED_CHECK')


@dataclass(frozen=True, slots=True)
class SealedEvaluation:
    challenger_fingerprint: str
    champion_fingerprint: str
    accounting_ref: str
    provenance: Provenance
    checks: tuple[CheckResult, ...]
    seal: str

    def __post_init__(self):
        for v in (self.challenger_fingerprint, self.champion_fingerprint, self.accounting_ref, self.seal):
            require_sha(v)
        self.provenance.__post_init__()
        if type(self.checks) is not tuple or len({c.name for c in self.checks}) != len(self.checks):
            raise ValueError('JUDGE_DUPLICATE_CHECK')
        for c in self.checks:
            c.__post_init__()
        if self.seal != digest(self.body()):
            raise ValueError('JUDGE_SEAL_MISMATCH')

    def body(self):
        return {k: v for k, v in asdict(self).items() if k != 'seal'}

    @classmethod
    def build(cls, challenger: Challenger, accounting_ref: str,
              provenance: Provenance, checks: tuple[CheckResult, ...]):
        challenger.__post_init__()
        if challenger.stage != 'CHAMPION_COMPARE':
            raise ValueError('CHALLENGER_NOT_EVALUATED')
        args = dict(challenger_fingerprint=digest(asdict(challenger)),
                    champion_fingerprint=challenger.champion_fingerprint,
                    accounting_ref=accounting_ref, provenance=provenance,
                    checks=tuple(sorted(checks, key=lambda c: c.name)))
        body = {**args, 'provenance': asdict(provenance), 'checks': [asdict(c) for c in args['checks']]}
        return cls(**args, seal=digest(body))


def judge(challenger: Challenger, bundle: SealedEvaluation, *, reviewer_id: str,
          expected_accounting_ref: str, now: str,
          independent_checks: tuple[CheckResult, ...] = ()) -> dict:
    authorize('G', 'VETO_PROMOTION')
    token(reviewer_id)
    bundle.__post_init__()
    challenger.__post_init__()
    if reviewer_id == challenger.hypothesis.proposer_id:
        raise PermissionError('PROPOSER_CANNOT_JUDGE')
    if (bundle.challenger_fingerprint != digest(asdict(challenger))
            or bundle.champion_fingerprint != challenger.champion_fingerprint
            or bundle.accounting_ref != expected_accounting_ref):
        raise ValueError('JUDGMENT_IDENTITY_MISMATCH')
    checks = {c.name: c for c in bundle.checks}
    failures = sorted(name for name, c in checks.items() if c.status == 'FAIL')
    missing = sorted(set(CHECKS)-checks.keys() | {name for name, c in checks.items() if c.status == 'UNKNOWN'})
    reproduced = {c.name: c for c in independent_checks}
    if len(reproduced) != len(independent_checks):
        raise ValueError('JUDGE_DUPLICATE_REPRODUCTION')
    for c in independent_checks:
        c.__post_init__()
        if c.status == 'FAIL' or (c.name in checks and c.status != checks[c.name].status):
            failures.append('INDEPENDENT_' + c.name)
        if c.name in checks and c.evidence_ref != checks[c.name].evidence_ref:
            failures.append('INDEPENDENT_SOURCE_' + c.name)
    for name in ('OOS', 'COST_2', 'LOOKAHEAD', 'SAFETY'):
        if name not in reproduced or reproduced[name].status != 'PASS':
            missing.append('INDEPENDENT_' + name)
    if not bundle.provenance.matches(challenger.hypothesis.provenance, now=now,
                                     scopes=('SYNTHETIC', 'REPLAY', 'LOCAL_TEST', 'CI')):
        missing.append('FRESH_COMPATIBLE_EVIDENCE')
    # Synthetic success validates plumbing, not deployable statistical evidence.
    if challenger.hypothesis.exploratory or bundle.provenance.evidence_scope != 'REPLAY':
        missing.append('CONFIRMATORY_REAL_DATA_REPLAY_REQUIRED')
    verdict = 'REJECT' if failures else 'MORE_EVIDENCE_REQUIRED' if missing else 'PROMOTION_CANDIDATE'
    return research_payload('INDEPENDENT_JUDGMENT', verdict=verdict, reviewer_id=reviewer_id,
                            proposer_id=challenger.hypothesis.proposer_id,
                            evidence_seal=bundle.seal, failed_checks=failures,
                            missing_checks=missing, actual_promotion=False)


def reproduce_core_checks(hypothesis, *, oos_gross_r: tuple, oos_cost_r: tuple,
                          causal_values: tuple, cutoff: int, evaluator,
                          champion_before, champion_after) -> tuple[CheckResult, ...]:
    """G computes selected checks from pinned inputs, never proposer verdicts.

    Host supplies a trusted pure evaluator from the sealed checkout. Arbitrary
    Python is not sandboxed by this API; source identity/permissions belong to
    the runner. Full statistical checks remain required by judge().
    """
    from daxlab.research.turbo_contract import finite, count
    from daxlab.research.turbo_experiment import ChampionIdentity, causal_prefix_probe
    hypothesis.__post_init__()
    count(len(oos_gross_r), 1, 100000)
    if len(oos_gross_r) != len(oos_cost_r) or not oos_gross_r:
        raise ValueError('INDEPENDENT_DATA_ALIGNMENT')
    for value in oos_gross_r:
        finite(value)
    for value in oos_cost_r:
        finite(value, 0)
    if type(champion_before) is not ChampionIdentity or type(champion_after) is not ChampionIdentity:
        raise ValueError('CHAMPION_IDENTITY_REQUIRED')
    results = []
    for name, factor in (('OOS', 1.0), ('COST_2', 2.0)):
        net = sum(g-factor*c for g, c in zip(oos_gross_r, oos_cost_r))
        status = ('UNKNOWN' if len(oos_gross_r) < hypothesis.minimum_sample
                  else 'PASS' if net > hypothesis.minimum_oos_net_r else 'FAIL')
        ref = digest({'gross': oos_gross_r, 'costs': oos_cost_r, 'factor': factor,
                      'hypothesis': hypothesis.fingerprint})
        results.append(CheckResult(name, status, ref, 'INDEPENDENT_NET_AFTER_COST'))
    probe = causal_prefix_probe(evaluator, causal_values, cutoff=cutoff)
    results.append(CheckResult('LOOKAHEAD', probe['status'], digest(probe), 'INDEPENDENT_PREFIX_PERTURBATION'))
    before, after = champion_before.fingerprint, champion_after.fingerprint
    results.append(CheckResult('SAFETY', 'PASS' if before == after else 'FAIL',
                                digest((before, after)), 'INDEPENDENT_CHAMPION_BINDING'))
    return tuple(results)


def publish_judgment(ledger, challenger: Challenger, bundle: SealedEvaluation, *,
                     reviewer_id: str, expected_head: str, now: str,
                     independent_checks: tuple[CheckResult, ...]) -> dict:
    """G's durable entrance verifies actual journal accounting, then appends.

    Low-level judge() is a deterministic reducer, not a publication authority.
    An unjournalled/self-asserted accounting hash cannot pass this entrance.
    """
    from daxlab.research.turbo_experiment import check_trial_accounting
    from daxlab.research.variant_trial_registry import TrialDeclaration
    rows = ledger.read(expected_head=expected_head)
    h = challenger.hypothesis
    declared = [r for r in rows if r['kind'] == 'HYPOTHESIS' and r['record_id'] == h.hypothesis_id]
    evaluations = [r for r in rows if r['record_id'] == h.hypothesis_id+'.evaluation' and r['kind'] == 'RESULT']
    if (len(declared) != 1 or digest(declared[0]['body']) != h.fingerprint or len(evaluations) != 1
            or digest(evaluations[0]['body']['bundle']) != digest(asdict(bundle))):
        raise ValueError('JUDGMENT_JOURNAL_BINDING')
    trials = tuple(TrialDeclaration(**r['body']) for r in rows if r['kind'] == 'TRIAL'
                   and r['body'].get('hypothesis_trial_id') == h.hypothesis_id)
    accounting = check_trial_accounting(h, trials, tuple(tuple(x) for x in evaluations[0]['body']['outcomes']),
                                       budget=len(h.trial_ids))
    result = judge(challenger, bundle, reviewer_id=reviewer_id, expected_accounting_ref=accounting,
                   now=now, independent_checks=independent_checks)
    pin = ledger.append(role='G', kind='JUDGMENT', record_id=h.hypothesis_id+'.judgment',
        body=result | {'independent_checks': [asdict(c) for c in independent_checks]}, expected_head=expected_head)
    return result | {'ledger_head': pin}


def judge_risk_report(spec, *, report: dict, gross_r: tuple, cost_r: tuple,
                      regimes: tuple, splits: tuple, provenance: Provenance,
                      proposer_id: str, reviewer_id: str) -> dict:
    """G reproduces the pinned risk experiment, rejecting any altered report.

    Same model semantics, separate evaluation. Statistical independence needs
    held-out data, not a second random seed. Never promotes a risk policy.
    """
    from daxlab.research.turbo_risk import evaluate_risk_research
    token(proposer_id)
    token(reviewer_id)
    if proposer_id == reviewer_id:
        raise PermissionError('PROPOSER_CANNOT_JUDGE')
    reproduced = evaluate_risk_research(spec, gross_r=gross_r, cost_r=cost_r,
                                       regimes=regimes, splits=splits, provenance=provenance)
    if digest(report) != digest(reproduced):
        raise ValueError('RISK_REPORT_REPRODUCTION_MISMATCH')
    return research_payload('RISK_INDEPENDENT_JUDGMENT', reviewer_id=reviewer_id,
        proposer_id=proposer_id, evidence_seal=digest(report),
        judgments=[{'label': c['label'], 'verdict': 'REJECT' if c['failures']
                    else 'MORE_EVIDENCE_REQUIRED', 'failures': c['failures']}
                   for c in reproduced['candidates']],
        limitation='TRADE_BOUNDARY_RESEARCH_NOT_NATIVE_ECONOMICS_OR_POLICY_PROMOTION')


def review_opportunity(observation, *, report: dict, proposer_id: str, reviewer_id: str) -> dict:
    from daxlab.research.turbo_risk import evaluate_opportunity
    token(proposer_id)
    token(reviewer_id)
    if proposer_id == reviewer_id:
        raise PermissionError('PROPOSER_CANNOT_JUDGE')
    reproduced = evaluate_opportunity(observation)
    if digest(report) != digest(reproduced):
        raise ValueError('OPPORTUNITY_REPRODUCTION_MISMATCH')
    return research_payload('OPPORTUNITY_REVIEW', reviewer_id=reviewer_id,
        proposer_id=proposer_id, observation_fingerprint=reproduced['observation_fingerprint'],
        provenance_fingerprint=observation.provenance.fingerprint,
        verdict='REJECT' if reproduced['opportunity_mode'] == 'TURBO_BLOCKED'
                else 'MORE_EVIDENCE_REQUIRED', evidence_seal=digest(report),
        limitation='QUALITY_SCREEN_REPRODUCED_NOT_RISK_POLICY_APPROVAL')
