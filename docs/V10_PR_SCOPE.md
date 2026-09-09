# V10 PR Validation Scope

This pull request contains offline-only SHADOW soak hardening and PAPER contract preparation.

CI acceptance requires:
- Ruff clean;
- full pytest clean;
- recovery reconstruction preflight clean;
- research registry and hypothesis ledger integrity clean;
- web-status truthfulness clean;
- frozen V11.2 engine probe and guarded replay smoke clean;
- 30-session / 3,090-bar synthetic SHADOW soak smoke clean.

Non-negotiable boundaries:
- synthetic evidence is not broker evidence;
- real MT5 milestones 102–110 remain open;
- Paper remains not started;
- no broker adapter or order submission function exists;
- LIVE remains unauthorized;
- V11.2 remains the immutable active reference;
- research candidates remain research.
