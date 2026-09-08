# V5 Clean Reference Reproduction — 2026-09-08

Status: VERIFIED REPRODUCTION / V11.2 UNCHANGED

## Result
The canonical active V11.2 reference was reproduced from the hash-verified 2014–2019 session surface and frozen exact candidate engine source.

Canonical schedule: rolling fixed 45 train / 20 OOS / 20 step, 81 windows.

Observed aggregates:
- normal: 856 OOS trades, -31.309210619787684 R, 37 positive WF, 44 negative WF, median WF PF 0.9057693102560179;
- stress 1.5x: 856 trades, -40.92169502338753 R, median WF PF 0.8909162959672307;
- stress 2x: 856 trades, -48.424611963007294 R, median WF PF 0.8766802664631563.

## Exact artifact reproduction
- WF metrics: 243 rows, SHA-256 `4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a` — exact match to frozen reference hash.
- Selected variants: 81 rows, SHA-256 `8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e` — exact match to frozen reference hash.
- Normal OOS trades: 856 rows, SHA-256 `f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023` — newly reproduced evidence; no historical frozen trade hash existed.

Recovery ZIP SHA-256: `f037cfe47a2d152884d7d803e51762cda83230093d6841b66a1d8cfadcc9ca35`.
A redundant copy is stored in the audited-data Drive folder as `V112_CLEAN_REFERENCE_EVIDENCE_2026_09_08.zip`.

## Accelerator
A separate research-only NumPy signal harness was validated on 240 deterministic sample days spanning 2014–2019 (960 OR/entry cases) with 0 signal mismatches against the frozen exact function. The complete fixed-reference run then reproduced both frozen detail hashes and all active aggregate values. Observed end-to-end runtime with trade export was approximately 25 seconds in the V5 runtime.

This accelerator is not a modification or promotion of V11.2. FAST/accelerated paths remain subordinate to exact/parity evidence.

## Forensic correction
The frozen engine payload's standalone `main()` builds an expanding training schedule and also contains empty-OOS reporting edge cases. It is not the canonical active-reference runner. The active reference is defined by `src/daxlab/reference/reference_runner.py`, which explicitly uses the fixed rolling 45/20/20 schedule. Expand-run checkpoints produced during V5 are forensic-only and must never be imported as active-reference evidence.

## Database decision
Do not mutate the production detail registry merely because the new trade hash now exists. First update the evidence/import contract and exercise the complete pre-import, transaction, idempotency and post-import reconciliation flow in an isolated schema. Production detail state remains fail-closed until that drill is green.
