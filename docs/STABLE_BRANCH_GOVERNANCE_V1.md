# Stable Branch Governance V1

Status: VERIFIED AUDIT / MANUAL-ADMIN ENFORCEMENT PENDING
Updated: 2026-09-12

Purpose: define the smallest reliable protection boundary for stable branch `main` without blocking ordinary development or misusing path-filtered CI checks.

## 1. Verified current state

Repository: `hennebergtoni-lgtm/dax-Day`
Stable branch: `main`
Observed main SHA during Step 2136: `e0784ebfc11bee28475fd9c3385be661af58a738`

Read-only GitHub evidence on 2026-09-12:

- normal branch metadata reports `protected=false`;
- normal branch metadata reports `protection.enabled=false`;
- normal branch metadata reports no required status checks;
- repository rulesets endpoint returns an empty list `[]`;
- the connected GitHub integration receives HTTP 403 on the branch-protection administration endpoint and does not expose a write action for branch protection/rulesets.

Therefore `main` is currently **not protected by an observable branch-protection rule or repository ruleset**, and this ChatGPT/GitHub connection cannot safely enforce one.

## 2. Minimal target protection

When repository administration is available, prefer this minimum stable-branch guard:

1. require changes to `main` to arrive through a pull request;
2. require the broad GitHub Actions check named `test` to pass before merge;
3. block force pushes to `main`;
4. block deletion of `main`;
5. do not require a fixed number of approving reviewers unless the repository has a reviewer workflow that will not deadlock a solo-maintainer repository;
6. do not universally require the `candidate-core` check.

### Why `test` is the universal required check

`test` is the job owned by `research-lab-ci`, which runs as the broad repository integration/regression gate on pull requests. It covers repository-wide tests plus recovery/research/web/runtime/reference/SHADOW integration checks.

### Why `candidate-core` is not universal

`candidate-core` is owned by `dax-bot-1x-ci`, whose workflow is intentionally path-filtered to Candidate/broker/operator surfaces. A documentation-only or unrelated valid PR may not trigger it. Requiring it globally could leave such PRs waiting forever for a check that was correctly skipped.

Candidate-related changes should still receive `candidate-core` whenever its path filters trigger.

## 3. Explicit non-goals

This governance rule does not:

- authorize PAPER or LIVE;
- change strategy logic;
- change runtime execution capability;
- merge PR #109;
- require multi-reviewer bureaucracy before the project has that operating model;
- replace CI ownership documented in `docs/CI_OWNERSHIP_CONTRACT_V1.md`.

## 4. Enforcement state

Current state: **WAITING_EXTERNAL / MANUAL_GITHUB_ADMIN**.

Reason: repository-side evidence is sufficient to define the desired rule, but the connected integration cannot administer branch protection or rulesets. Do not claim `main` is protected until fresh GitHub branch/ruleset evidence proves the rule is active.

When an authorized repository-admin action becomes available, apply the minimum target protection, then re-read:

- `/branches/main`;
- `/branches/main/protection` when authorized;
- `/rulesets`;
- a representative PR check suite.

Only after that readback may the status become VERIFIED / ENFORCED.

## 5. Drift rule

Any later change to required-check names or CI ownership must be reconciled with this governance document before stable-branch protection is changed. In particular, if the universal broad integration job stops being named `test`, update the protection rule and this document together.
