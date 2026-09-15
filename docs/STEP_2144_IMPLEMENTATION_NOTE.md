# Step 2144 — Research Promotion Contract

Status: **COMPLETED / CI VERIFIED**

Step 2144 defines deterministic research provenance and software-artifact promotion metadata only. It does not change strategy behavior, runtime connectivity, or any external action capability.

Implemented surface:

- reuses the established `ExperimentManifest`, `WalkForwardSpec` and `CostModel` provenance primitives rather than redefining them;
- adds `EvaluationContractV1` for explicit split/WF, cost-model and fill-assumption identity;
- adds `ResearchExperimentV1` binding strategy/config identity, dataset and dataset-manifest fingerprints, evaluation identity, robustness-evidence references, source commit and limitations;
- adds a deterministic `ProductStrategyArtifactV1` with tamper-checked artifact fingerprint;
- adds `ResearchPromotionArtifactV1` with explicit promotion state and canonical JSON persistence;
- carries fail-closed safety fields: `execution_capability="NONE"`, `order_execution_authorized=false`, `paper_authorized=false`, `live_authorized=false`;
- adds regression coverage for deterministic identities, evidence/config drift, canonical JSON, tamper detection, fail-closed authorization and forbidden runtime/MT5/CAND-001 dependencies.

Evidence head: `b4f7152bff59ee85aa459348e6b72219d597df89`

CI evidence:

- `dax-bot-1x-ci` #373 — GREEN
- `research-lab-ci` #1157 — GREEN

No optimizer/search engine, broker connection, strategy-rule change, economic promotion claim, PAPER authorization or LIVE authorization was introduced.
