# V6 Research Run Recovery Contract

Status: BINDING RESEARCH CONTRACT

## Step 41 — Material research artifact recovery
Every evidence-producing research run must retain enough state to reconstruct or safely reject the run:
- immutable run manifest
- source commit SHA
- dataset fingerprint
- engine fingerprint
- research-family / hypothesis id
- config fingerprint
- run status
- checkpoint/resume state when applicable
- result artifact hashes
- decision/selection summary
- exact/parity status for accelerated paths

Temporary notebook/session state is never the sole source of truth.

## Step 42 — Run identity and resume linkage
Each material run receives an immutable `run_id` derived from or bound to its canonical identity surface. A resumed or derived run records `parent_run_id` plus the exact last completed checkpoint/WF/date. Resume is allowed only when dataset, engine, config and research-definition fingerprints match.

Changing any identity-bearing input creates a new run, not a continuation.

## Recovery states
- RUNNING
- COMPLETED
- ABORTED
- INVALIDATED

A process interruption is not equivalent to COMPLETED.

## Research result bundle
A material bundle should include where applicable:
- run_manifest.json
- checkpoint.json
- result.json / CSV artifacts
- feature-bundle manifest
- SHA256SUMS
- family/hypothesis definition version
- exact spot-check report
- negative/neutral findings

## Failure rules
- missing identity fingerprint => fail closed
- checkpoint/config drift => reject resume
- missing result hash => do not import/promote
- partial artifact set => PARTIAL / not verified
- recovered output without matching definition version => new forensic artifact, not canonical continuation

## Storage principle
Versioned Git metadata/contracts + durable result storage + DB registry may reinforce each other, but no single transient system is allowed to be the only recovery path.
